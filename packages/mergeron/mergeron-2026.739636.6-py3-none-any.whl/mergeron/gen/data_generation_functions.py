"""Non-public functions called in data_generation.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
from attrs import evolve
from joblib import Parallel, delayed, parallel_config  # type: ignore

if TYPE_CHECKING:
    from numpy.random import Generator, SeedSequence
    from numpy.typing import NDArray

    from ..core import EmpiricalMarginData

from .. import (
    DEFAULT_REC,
    EMPTY_ARRAYDOUBLE,
    VERSION,
    ArrayBoolean,
    ArrayDouble,
    ArrayFloat,
    ArrayUINT8,
    RECForm,
)
from ..core.pseudorandom_numbers import MultithreadedRNG, prng
from . import (
    DEFAULT_DIR_COND_DIST_PARMS,
    HSR_BETA_PARMS,
    HSR_RATIO,
    SUBSAMPLE_SIZE,
    MarginsData,
    MarketSharesData,
    MarketShareSpec,
    PCMDistribution,
    PCMRestriction,
    PCMSpec,
    PricesData,
    PriceSpec,
    SeedSequenceData,
    SHRDistribution,
    SSZConstant,
)

__version__ = VERSION


def market_share_sampler(
    _share_spec: MarketShareSpec,
    _sample_size: int,
    _seed_data: SeedSequenceData,
    _nthreads: int,
    /,
) -> MarketSharesData:
    """Generate share data.

    Parameters
    ----------
    _share_spec
        Class specifying parameters for generating market share data

    _sample_size
        Number of market shares to generate

    _seed_data
        List of seed sequences, including seeds for generating firm-counts
        and market shares from firm-counts

    _nthreads
        Must be specified for generating repeatable random streams

    Returns
    -------
    Arrays representing shares, diversion ratios, etc. structured as
    a :class:`gen.MarketSharesData` object.

    """
    dist_type_mktshr, dist_parms_mktshr, share_lower_bound, recapture_form = (
        getattr(_share_spec, _f)
        for _f in ("dist_type", "dist_parms", "lower_bound", "recapture_form")
    )

    _fcount_rng_seed_seq = _seed_data.fcounts
    _mktshr_rng_seed_seq = _seed_data.share

    if dist_type_mktshr == SHRDistribution.UNI:
        mkt_share_sample = MarketSharesData(
            mktshr_array=market_share_sampler_uniform(
                dist_parms_mktshr,
                (_sample_size, 2),
                share_lower_bound,
                _mktshr_rng_seed_seq,
                _nthreads,
            )
        )
    elif dist_type_mktshr.name.startswith("DIR_"):
        mkt_share_sample = _market_share_sampler_dirichlet_pooled(
            _share_spec,
            _sample_size,
            _fcount_rng_seed_seq,
            _mktshr_rng_seed_seq,
            _nthreads,
        )

    else:
        raise ValueError(
            f'Unexpected type, "{dist_type_mktshr}" for share distribution.'
        )

    # If recapture_form == "inside-out", recalculate _aggregate_purchase_prob
    if recapture_form == RECForm.INOUT:
        r_bar_ = _share_spec.recapture_rate or DEFAULT_REC
        mkt_share_sample = evolve(
            mkt_share_sample,
            aggregate_purchase_prob=(  # assigning r_bar to the smaller merging firm
                r_bar_
                / (
                    1.0
                    - (1.0 - r_bar_)
                    * mkt_share_sample.mktshr_array[:, :2].min(axis=1, keepdims=True)
                )
            ),
        )

    return mkt_share_sample


def market_share_sampler_uniform(
    _dist_parms_mktshr: NDArray[np.floating],
    _s_size: tuple[int, int],
    _share_lower_bound: float,
    _mktshr_rng_seed_seq: SeedSequence,
    _nthreads: int,
    /,
) -> ArrayDouble:
    """Generate merging-firm shares from Uniform distribution on the 3-D simplex.

    Parameters
    ----------
    _s_size
        size of sample to be drawn

    _mktshr_rng_seed_seq
        seed for rng, so results can be made replicable

    _nthreads
        number of threads for random number generation

    Returns
    -------
        generated market shares

    """
    _row_count, _ncols = _s_size
    _s_sizeup = int(np.ceil(1.1 * _row_count / _nthreads) * _nthreads)
    mktshr_array = ArrayDouble(np.empty((_s_sizeup, _ncols)))

    MultithreadedRNG(
        mktshr_array,
        dist_type="Uniform",
        dist_parms=_dist_parms_mktshr,
        seed_sequence=_mktshr_rng_seed_seq,
        nthreads=_nthreads,
    ).fill()

    # Convert draws on U[0, 1] to Uniformly-distributed draws on simplex, s_1 + s_2 <= 1
    mktshr_array = np.hstack((
        mktshr_array.min(axis=1, keepdims=True),
        np.abs(np.diff(mktshr_array, axis=1)),
    ))

    # Keep only share combinations with minimum share lower bound
    return ArrayDouble(
        mktshr_array[mktshr_array.min(axis=1) > _share_lower_bound][:_row_count]
    )


def _market_share_sampler_dirichlet_pooled(
    _share_spec: MarketShareSpec,
    _s_size: int,
    _fcount_rng_seed_seq: SeedSequence | None,
    _mktshr_rng_seed_seq: SeedSequence,
    _nthreads: int,
    /,
) -> MarketSharesData:
    """Dirichlet-distributed shares with multiple firm-counts.

    Firm-counts may be specified as having Uniform distribution over the range
    of firm counts, or a set of probability weights may be specified. In the
    latter case the proportion of draws for each firm-count matches the
    specified probability weight.

    Parameters
    ----------
    _share_spec
        market share specification

    _s_size
        sample size to be drawn

    _fcount_rng_seed_seq
        seed firm count rng, for replicable results

    _mktshr_rng_seed_seq
        seed market share rng, for replicable results

    _nthreads
        number of threads for parallelized random number generation

    Returns
    -------
        array of market shares and other market statistics

    """
    (
        _firm_count_wts,
        _share_lower_bound,
        _dist_type_dir,
        _dist_parms_dir,
        _recapture_form,
    ) = (
        getattr(_share_spec, _f)
        for _f in (
            "firm_counts_weights",
            "lower_bound",
            "dist_type",
            "dist_parms",
            "recapture_form",
        )
    )
    min_choice_wt = 0.03 if _dist_type_dir == SHRDistribution.DIR_FLAT_CONSTR else 0.00
    fcount_keys, choice_wts = zip(
        *(
            f_
            for f_ in zip(
                2 + np.arange(len(_firm_count_wts), dtype=np.uint8),
                _firm_count_wts / _firm_count_wts.sum(),
                strict=True,
            )
            if f_[1] > min_choice_wt
        ),
        strict=True,
    )
    choice_wts = (_n := np.asarray(choice_wts)) / _n.sum()
    fcount_keys = ArrayUINT8(fcount_keys)  # type: ignore

    fc_max = fcount_keys[-1]
    dir_alphas_full = ArrayFloat(
        _dist_parms_dir[:fc_max] if len(_dist_parms_dir) else [1.0] * fc_max
    )
    mktshr_array_ = ArrayDouble(np.empty((_s_size, fc_max)))
    nth_firm_share_ = ArrayDouble(np.empty((_s_size, 1)))
    aggregate_purchase_prob_ = EMPTY_ARRAYDOUBLE

    mktshr_seed_seq_ch = _mktshr_rng_seed_seq.spawn(len(fcount_keys))

    if _recapture_form == RECForm.OUTIN:
        fcount_keys += 1
        aggregate_purchase_prob_ = ArrayDouble(np.empty((_s_size, 1)))

    fcounts_ = prng(_fcount_rng_seed_seq).choice(
        fcount_keys, size=(_s_size, 1), p=choice_wts
    )

    for _f_val, _f_seed in zip(fcount_keys, mktshr_seed_seq_ch, strict=True):
        fcounts_match_rows = np.where(fcounts_ == _f_val)[0]
        _sub_ssz = len(fcounts_match_rows)
        dir_alphas_test = _dir_alphas_builder(dir_alphas_full, _f_val, _dist_type_dir)

        mktshr_array_f = market_share_sampler_dirichlet(
            dir_alphas_test, _share_lower_bound, _sub_ssz, _f_seed, _nthreads
        )

        fcounts_f = np.full((_sub_ssz, 1), _f_val, np.uint8)
        if _recapture_form == RECForm.OUTIN:
            fcounts_f -= 1
            aggregate_purchase_prob_f = 1 - mktshr_array_f[:, [-1]]
            try:
                np.testing.assert_array_almost_equal(
                    mktshr_array_f[:, :-1].sum(axis=1, keepdims=True),
                    aggregate_purchase_prob_f,
                )
            except AssertionError as _e:
                print(_f_val - 1)
                print(mktshr_array_f[:, :-1].shape, aggregate_purchase_prob_f.shape)
                print(
                    mktshr_array_f[:, :-1].sum(axis=1, keepdims=True),
                    aggregate_purchase_prob_f,
                )
                raise ValueError(
                    "DATA GENERATION ERROR: {}".format(
                        "Choice probabilities don't add to aggregate choice probabilities."
                    )
                ) from _e

            mktshr_array_f = mktshr_array_f[:, :-1] / aggregate_purchase_prob_f
            # If recapture_form is not 'outside_in', then
            # aggregate_purchase_prob_ is calculated downstream, leave it empty
            aggregate_purchase_prob_[fcounts_match_rows] = aggregate_purchase_prob_f

        # Push data for present sample to parent
        fcounts_[fcounts_match_rows] = fcounts_f
        nth_firm_share_[fcounts_match_rows] = mktshr_array_f[:, [-1]]
        mktshr_array_[fcounts_match_rows] = np.pad(
            mktshr_array_f, ((0, 0), (0, fc_max - mktshr_array_f.shape[1])), "constant"
        )

    # Test market share array
    if (iss_ := np.round(np.einsum("ij->", mktshr_array_))) != _s_size or iss_ != len(
        mktshr_array_
    ):
        raise ValueError(
            "DATA GENERATION ERROR: {} {} {}".format(
                "Generation of sample shares is inconsistent:",
                "array of drawn shares must some to the number of draws",
                "i.e., the sample size, which condition is not met.",
            )
        )
    if _recapture_form == RECForm.OUTIN:
        try:
            np.testing.assert_array_almost_equal(
                np.einsum("ij,ij->ij", aggregate_purchase_prob_, mktshr_array_).sum(
                    axis=1, keepdims=True
                ),
                aggregate_purchase_prob_,
            )
        except AssertionError as _e:
            raise ValueError(
                "DATA GENERATION ERROR: {}".format(
                    "Choice probabilities don't add to aggregate choice probabilities."
                )
            ) from _e

    return MarketSharesData(
        mktshr_array_, fcounts_, nth_firm_share_, aggregate_purchase_prob_
    )


def _dir_alphas_builder(
    _dir_alphas: NDArray[np.floating], _fcv: int, _dist_type: SHRDistribution
) -> ArrayFloat:

    if _dist_type == SHRDistribution.DIR_COND:
        _theta_1, _theta_2, _Theta = _dir_alphas
        _m, _r = 2, _fcv - 2  # merging-firm count, non-merging firm-count
        return ArrayFloat([_theta_1, _theta_2] + ([] if not _r else [_Theta / _r] * _r))

    return ArrayFloat(_dir_alphas[:_fcv])


def market_share_sampler_dirichlet(
    _dir_alphas: NDArray[np.floating],
    _share_lower_bound: float,
    _s_size: int,
    _mktshr_rng_seed_seq: SeedSequence,
    _nthreads: int,
    /,
) -> ArrayDouble:
    """Dirichlet-distributed shares with fixed firm-count.

    Parameters
    ----------
    _dir_alphas
        Shape parameters for Dirichlet distribution

    _s_size
        sample size to be drawn

    _mktshr_rng_seed_seq
        seed market share rng, for replicable results

    _nthreads
        number of threads for parallelized random number generation

    Returns
    -------
        array of market shares and other market statistics

    """
    if not isinstance(_dir_alphas, np.ndarray):
        _dir_alphas = np.array(_dir_alphas)

    _cond_dir_test = all((
        np.array_equal(_dir_alphas[:2], DEFAULT_DIR_COND_DIST_PARMS[:2]),
        np.isclose(_dir_alphas.sum(), DEFAULT_DIR_COND_DIST_PARMS.sum()),
    ))

    _ncols = len(_dir_alphas)
    # Scale up to reach specified sample size after restricting
    # minimum share to 1e-2
    # except the minimum can't be met for conditional Dirichlet distribution
    if _cond_dir_test:
        _s_sizeup = _s_size
    elif _share_lower_bound <= 1e-3:
        _s_sizeup = int(_s_size * 1.1)
    elif _share_lower_bound <= 1e-2:
        _s_sizeup = int(
            {
                3: 1.073,
                4: 1.14,
                5: 1.239,
                6: 1.372,
                7: 1.554,
                8: 1.804,
                9: 2.139,
                10: 2.594,
            }.get(_ncols, 3.0)
            * _s_size
            + 1e4  # adjust up for small samples
        )
    else:
        raise ValueError(
            "DATA GENERATION ERROR: {}".format(
                "Minimum market share tolerance greater than 1% is not supported. "
                f"Got, {_share_lower_bound:.2%}."
            )
        )
    # adjust scaler for number of threads
    _s_sizeup = int(np.ceil(_s_sizeup / _nthreads) * _nthreads)
    mktshr_array = ArrayDouble(np.empty((_s_sizeup, _ncols)))
    MultithreadedRNG(
        mktshr_array,
        dist_type="Dirichlet",
        dist_parms=_dir_alphas,
        seed_sequence=_mktshr_rng_seed_seq,
        nthreads=_nthreads,
    ).fill()

    # Shares concentrated toward merging-firms, so
    # we don't need to test minimum against tolerance
    mktshr_array = (
        mktshr_array[:_s_size]
        if _cond_dir_test
        else mktshr_array[mktshr_array.min(axis=1) > _share_lower_bound,][:_s_size]
    )

    if (iss_ := np.round(np.einsum("ij->", mktshr_array))) != _s_size or iss_ != len(
        mktshr_array
    ):
        print(_dir_alphas)
        print("Sample size:", _ncols, _s_size, _s_sizeup)
        print(
            repr(_s_size), iss_, len(mktshr_array), _share_lower_bound, _cond_dir_test
        )
        print(repr(mktshr_array[-10:, :]))
        raise ValueError(
            "DATA GENERATION ERROR: {} {} {}".format(
                "Generation of sample shares is inconsistent:",
                "array of drawn shares must sum to the number of draws",
                "i.e., the sample size, which condition is not met.",
            )
        )

    return mktshr_array  # type: ignore


def diversion_ratios_builder(
    _recapture_form: RECForm,
    _recapture_rate: float | None,
    _mktshr_array: ArrayDouble,
    _aggregate_purchase_prob: ArrayDouble,
    /,
) -> ArrayDouble:
    """
    Given merging-firm shares and related parameters, return diversion ratios.

    If recapture is specified as :attr:`mergeron.RECForm.OUTIN`, then the
    choice-probability for the outside good must be supplied.

    Parameters
    ----------
    _recapture_form
        Enum specifying Fixed (proportional), Inside-out, or Outside-in

    _recapture_rate
        If recapture is proportional or inside-out, the recapture rate
        for the firm with the smaller share.

    _mktshr_array
        Generated market shares.

    _aggregate_purchase_prob
        1 minus probability that the outside good is chosen; converts
        market shares to choice probabilities by multiplication.

    Raises
    ------
    ValueError
        If the firm with the smaller share does not have the larger
        diversion ratio between the merging firms.

    Returns
    -------
        Merging-firm diversion ratios for mergers in the sample.

    """
    divratio_array: ArrayDouble
    _frmshr_array = _mktshr_array[:, :2]

    if _recapture_form == RECForm.FIXED:
        if _recapture_rate is None:
            raise ValueError(
                "If recapture form is, RECForm.FIXED, a recapture rate must be supplied."
            )
        divratio_array = _recapture_rate * _frmshr_array[:, ::-1] / (1 - _frmshr_array)

    else:
        _purchase_prob = np.einsum("ij,ij->ij", _aggregate_purchase_prob, _frmshr_array)
        divratio_array = _purchase_prob[:, ::-1] / (1 - _purchase_prob)

    divr_assert_test = (
        (np.round(np.einsum("ij->i", _frmshr_array), 15) == 1)
        | (np.argmin(_frmshr_array, axis=1) == np.argmax(divratio_array, axis=1))
    )[:, None]
    if not all(divr_assert_test):
        print(_frmshr_array, divratio_array)
        raise ValueError(
            "{} {} {} {}".format(
                "Data construction fails tests:",
                "the index of min(s_1, s_2) must equal",
                "the index of max(d_12, d_21), for all draws.",
                "unless frmshr_array sums to 1.00.",
            )
        )

    return divratio_array


def prices_sampler(
    _share_spec: MarketShareSpec,
    _pcm_spec: PCMSpec,
    _price_spec: PriceSpec,
    _hsr_filing_test_type: SSZConstant,
    _market_share_sample: MarketSharesData,
    _seed_data: SeedSequenceData,
    _nthreads: int,
    /,
) -> tuple[MarginsData, PricesData]:
    """Generate margin and price data for mergers in the sample.

    Parameters
    ----------
    _share_spec
        Enum specifying whether to use asymmetric or flat margins; see
        :class:`mergeron.gen.MarketShareSpec`.
    _pcm_spec
        Enum specifying whether to use asymmetric or flat margins. see
        :class:`mergeron.gen.PCMSpec`.

    _price_spec
        Enum specifying whether to use symmetric, positive, or negative
        margins; see :class:`mergeron.gen.PriceSpec`.

    _hsr_filing_test_type
        Enum specifying restriction, if any, to impose on market data sample
        to model HSR filing requirements; see :class:`mergeron.gen.SSZConstant`.

    _market_share_sample
        :class:`MarketSharesData` for mergers in the sample.

    _seed_data
        List of seed sequences, including seeds for generating prices and
        margins, and a HSR filing test vector, as needed.

    _nthreads
        Number of threads to use in generating price data.

    Returns
    -------
        Simulated margin- and price-data arrays for mergers in the sample.
    """
    _pcm_rng_seed_seq, _pr_rng_seed_seq, _hsr_rng_seed_seq = (
        getattr(_seed_data, _a) for _a in ("pcm", "price", "hsr_filing_test")
    )

    _mktshr_array, _nth_firm_share, _aggregate_purchase_prob = (
        getattr(_market_share_sample, _a)
        for _a in ("mktshr_array", "nth_firm_share", "aggregate_purchase_prob")
    )

    price_array = ArrayDouble(np.ones_like(_mktshr_array))
    nth_firm_price = EMPTY_ARRAYDOUBLE
    margin_data = MarginsData(
        ArrayDouble(np.array([], float)), ArrayBoolean(np.array([], bool))
    )

    share_uni_flag = _share_spec.dist_type == SHRDistribution.UNI

    pr_max_number = 5
    if _price_spec == PriceSpec.SYM and not share_uni_flag:
        nth_firm_price = ArrayDouble(np.ones((len(_mktshr_array), 1)))
    elif _price_spec in {PriceSpec.POS, PriceSpec.NEG, PriceSpec.RND}:
        price_array, nth_firm_price = _share_correlated_number(
            _price_spec,
            pr_max_number,
            share_uni_flag,
            _mktshr_array,
            _nth_firm_share,
            seed_sequence=_pr_rng_seed_seq,
        )
    elif _price_spec == PriceSpec.CSY:
        if share_uni_flag:
            frmshr_array_plus = _mktshr_array
        else:
            frmshr_array_plus = np.hstack((_mktshr_array, _nth_firm_share)).view(
                ArrayDouble
            )
        # pcm_spec_here = evolve(_pcm_spec, pcm_restriction=PCMRestriction.IID)
        _pcm_scaler = 1.0
        margin_data = _margins_sampler(
            _pcm_spec,
            _price_spec,
            _pcm_scaler,
            frmshr_array_plus,
            _aggregate_purchase_prob,
            _pcm_rng_seed_seq,
            _nthreads,
        )

        pcm_array = margin_data.pcm_array
        price_array = np.divide(_pcm_scaler, 1 - pcm_array)
        if not share_uni_flag:
            nth_firm_price, price_array = price_array[:, -1:], price_array[:, :-1]
            pcm_array = pcm_array[:, :-1]

        margin_data = MarginsData(pcm_array, margin_data.mnl_test)
    elif _price_spec != PriceSpec.SYM:
        raise ValueError(
            f'Specification of price distribution, "{_price_spec.value}" is invalid.'
        )
    margin_data = (
        margin_data
        if margin_data.pcm_array.shape != (0,)
        else _margins_sampler(
            _pcm_spec,
            _price_spec,
            price_array,
            _mktshr_array,
            _aggregate_purchase_prob,
            _pcm_rng_seed_seq,
            _nthreads,
        )
    )

    if _hsr_filing_test_type.name.startswith("HSR_"):
        # _mfra: computed merging firms' revenues over sample
        _mfra = np.einsum("ij,ij->ij", price_array[:, :2], _mktshr_array[:, :2])

        if _hsr_filing_test_type in {SSZConstant.HSR_TEN, SSZConstant.HSR_TEN_UNI}:
            hsr_filing_test = (
                np.divide((_s := np.sort(_mfra, axis=1))[:, 1], _s[:, 0]) >= HSR_RATIO
            )
        elif _share_spec.dist_type != SHRDistribution.UNI:
            # The nth firm test implemented here avoids an automatic 10-to-1 revenue ratio restriction, we implement as :
            # if the smaller merging firm matches or exceeds the n-th firm in size, and
            # the larger merging firm has at least 10 times the size of the nth firm,
            # the size test is considered met.
            # Alternatively, if the smaller merging firm has 10% or greater share,
            # # the value of transaction test is considered met.
            if _hsr_filing_test_type == SSZConstant.HSR_RNDU:
                _hsr_test_share = np.empty_like(_nth_firm_share)
                MultithreadedRNG(
                    values=_hsr_test_share,
                    dist_type="Random",
                    seed_sequence=_hsr_rng_seed_seq,
                    nthreads=_nthreads,
                ).fill()
            elif _hsr_filing_test_type == SSZConstant.HSR_RNDB:
                _hsr_test_share = np.empty_like(_nth_firm_share)
                MultithreadedRNG(
                    values=_hsr_test_share,
                    dist_type="Beta",
                    dist_parms=HSR_BETA_PARMS,
                    seed_sequence=_hsr_rng_seed_seq,
                    nthreads=_nthreads,
                ).fill()
            else:
                _hsr_test_share = _nth_firm_share
            _hsr_test_rev = np.einsum("ij,ij->ij", nth_firm_price, _hsr_test_share)
            hsr_filing_test = (
                np.sort(_mfra, axis=1) / _hsr_test_rev >= [1, HSR_RATIO]
            ).sum(axis=1) == _mfra.shape[1]
            del _hsr_test_rev
        else:
            raise ValueError(
                f"Invalid value for _hsr_filing_test_type: {_hsr_filing_test_type} "
                f"with share distribution, {_share_spec.dist_type}."
            )
        del _mfra

    else:
        # Otherwise, all draws meet the filing test
        hsr_filing_test = np.full(len(_mktshr_array), True)

    return margin_data, PricesData(price_array, hsr_filing_test)


def _share_correlated_number(
    _correlation_spec: PriceSpec,
    _max_number: int,
    _share_uni_flag: bool,
    _share_array: ArrayDouble,
    _nth_firm_share: ArrayDouble,
    /,
    seed_sequence: SeedSequence | None,
) -> ArrayDouble:
    _nth_firm_price = ArrayDouble(np.array([], float))

    match _correlation_spec:
        case PriceSpec.POS:
            price_array = _sharelator(_share_array, _max_number)
            if not _share_uni_flag:
                _nth_firm_price = _sharelator(_nth_firm_share, _max_number)

        case PriceSpec.NEG:
            price_array = _sharelator(1 - _share_array, _max_number)  # type: ignore
            if not _share_uni_flag:
                _nth_firm_price = _sharelator(1 - _nth_firm_share, _max_number)  # type: ignore

        case PriceSpec.RND:
            _ncols = _share_array.shape[1] + (0 if _share_uni_flag else 1)
            price_array = ArrayDouble(
                prng(seed_sequence)
                .integers(1, _max_number + 1, size=(len(_share_array), _ncols))
                .astype(np.float64)
            )
            if not _share_uni_flag:
                _nth_firm_price, price_array = price_array[:, -1:], price_array[:, :-1]

        case _:
            raise ValueError(f"Invalid value here: {_correlation_spec}.")

    return price_array, _nth_firm_price  # type: ignore


def _sharelator(_share_array: ArrayDouble, _max_number: int = 5) -> ArrayDouble:
    return ArrayDouble(np.ceil(_share_array * 5.0) * _max_number / 5.0)


def _margins_sampler(
    _pcm_spec: PCMSpec,
    _price_spec: PriceSpec,
    _pcm_scaler: float | ArrayDouble,
    _mktshr_array: ArrayDouble,  # mc if PriceSpec.CSY else p
    _aggregate_purchase_prob: ArrayDouble,
    _pcm_rng_seed_seq: SeedSequence,
    _nthreads: int,
    /,
) -> MarginsData:
    _dist_type_pcm, _dist_parms_pcm, _pcm_restriction = (
        getattr(_pcm_spec, _f) for _f in ("dist_type", "dist_parms", "pcm_restriction")
    )

    pcm_array = (
        np.empty_like(_mktshr_array[:, :1])
        if _pcm_spec.pcm_restriction in {PCMRestriction.SYM, PCMRestriction.MNL}
        else np.empty_like(_mktshr_array)
    )

    loc_, scale_ = 0.0, 1.0
    if _dist_type_pcm == PCMDistribution.EMPR_M:
        pcm_array = _empirical_margin_resampler(
            _dist_parms_pcm,
            sample_size=pcm_array.shape,
            seed_sequence=_pcm_rng_seed_seq,
            nthreads=_nthreads,
        )

    else:
        dist_type_: Literal["Beta", "Uniform"]
        if _dist_type_pcm in {PCMDistribution.BETA, PCMDistribution.EMPR_U}:
            dist_type_ = "Beta"
            alpha_, beta_, loc_, scale_ = (
                beta_located_bound(_dist_parms_pcm)
                if _dist_type_pcm == PCMDistribution.EMPR_U
                else (*_dist_parms_pcm, loc_, scale_)
            )
            dist_parms_ = np.array([alpha_, beta_])

        else:
            dist_type_ = "Uniform"
            dist_parms_ = _dist_parms_pcm

        MultithreadedRNG(
            pcm_array,
            dist_type=dist_type_,
            dist_parms=dist_parms_,
            seed_sequence=_pcm_rng_seed_seq,
            nthreads=_nthreads,
        ).fill()

    if _dist_type_pcm == PCMDistribution.EMPR_U:
        pcm_array = loc_ + scale_ * pcm_array

    mnl_test = np.full(len(pcm_array), True)
    if _pcm_restriction == PCMRestriction.SYM:
        pcm_array = np.hstack((pcm_array,) * _mktshr_array.shape[1])
    elif _pcm_restriction == PCMRestriction.MNL:
        # Impose FOCs from profit-maximization with MNL demand
        purchase_prob_array = _aggregate_purchase_prob * _mktshr_array

        if _price_spec == PriceSpec.SYM:
            _pcm_array_row = np.divide(
                np.einsum(
                    "ij,ij->ij", pcm_array[:, :1], 1 - purchase_prob_array[:, :1]
                ),
                1 - purchase_prob_array[:, 1:],
            )

        elif _price_spec == PriceSpec.CSY:
            _nr_0 = np.divide(
                _pcm_scaler
                * np.einsum("ij,ij->ij", pcm_array[:, :1], purchase_prob_array[:, :1])
                if isinstance(_pcm_scaler, float)
                else np.einsum(
                    "ij,ij,ij->ij",
                    _pcm_scaler[:, :1],
                    pcm_array[:, :1],
                    purchase_prob_array[:, :1],
                ),
                1 - pcm_array[:, :1],
            )
            _dr_0 = (
                np.einsum(
                    "ij,ij->ij", _pcm_scaler[:, 1:], 1 - purchase_prob_array[:, 1:]
                )
                if isinstance(_pcm_scaler, ArrayDouble)
                else _pcm_scaler * (1 - purchase_prob_array[:, 1:])
            )
            _pcm_array_row = np.divide(_nr_0, _nr_0 + _dr_0)

        elif isinstance(_pcm_scaler, ArrayDouble):
            _pcm_array_row = np.divide(
                np.einsum(
                    "ij,ij,ij->ij",
                    _pcm_scaler[:, :1],
                    pcm_array[:, :1],
                    1 - purchase_prob_array[:, :1],
                ),
                np.einsum(
                    "ij,ij->ij", _pcm_scaler[:, 1:], 1 - purchase_prob_array[:, 1:]
                ),
            )

        else:
            raise ValueError(
                "Expected price array as second argument to _margins_sampler, got float."
            )

        pcm_array = np.hstack((pcm_array, _pcm_array_row))

        # Parallelize MNL test:
        # # mnl_test = np.logical_and(
        # # (pcm_array[:, 1:] >= 0).all(axis=1), (pcm_array[:, 1:] <= 1).all(axis=1)
        # # )

        iter_count = int((len(pcm_array) / SUBSAMPLE_SIZE).__ceil__())
        hmt_retval = Parallel(
            backend="threading",
            n_jobs=min(_nthreads, iter_count),
            return_as="generator",
        )(
            delayed(np.logical_and)(
                (
                    (
                        _p := pcm_array[
                            _idx * SUBSAMPLE_SIZE : (
                                min((_idx + 1) * SUBSAMPLE_SIZE, len(pcm_array))
                            ),
                            1:,
                        ]
                    )
                    >= 0
                ).all(axis=1),
                (_p <= 1).all(axis=1),
            )
            for _idx in range(iter_count)
        )
        mnl_test = np.concatenate(list(hmt_retval))

    # else:  # This is a no-op, so commented out

    return MarginsData(pcm_array, mnl_test)


def _empirical_margin_resampler(
    _dist_parms: EmpiricalMarginData,
    /,
    *,
    sample_size: int | tuple[int, int],
    seed_sequence: SeedSequence,
    nthreads: int,
) -> ArrayDouble:
    """Generate draws from the empirical distribution based on Prof. Damodaran's margin data.

    The empirical distribution is estimated across multiple years of data as the means and
    firm-counts (weights) by industry as reported in the source data. Firms in the
    finance, investment, insurance, reinsurance, and REITs (namely, firms providing financial services)
    are excluded from the sample used to estimate the empirical distribution.

    Parameters
    ----------
    _dist_parms
        Array of margins and firm counts, with array of summary statistics,
        extracted from Prof. Damodaran's margin data

    sample_size
        Number of draws; if tuple, (number of draws, number of columns)

    seed_sequence
        SeedSequence for seeding random-number generator when results
        are to be repeatable

    nthreads
        Number of threads to use in generating margin data.

    Returns
    -------
        Array of margin values

    """
    _ssz, _ncols = (sample_size, 0) if isinstance(sample_size, int) else sample_size
    _rng1, _rng2 = prng(seed_sequence).spawn(2)
    _s_sizeup = int(np.ceil(_ssz / nthreads) * nthreads)

    if _ncols < 2:
        ret_array = Parallel(
            backend="threading", n_jobs=nthreads, return_as="generator"
        )(
            delayed(_mgn_resampler)(_dist_parms, _s_sizeup, _rng1i, _rng2i)
            for _rng1i, _rng2i in zip(
                _rng1.spawn(nthreads), _rng2.spawn(nthreads), strict=True
            )
        )

        ret_array = np.concatenate(list(ret_array))[:_ssz]
        return ArrayDouble(ret_array if _ncols == 0 else ret_array[:, None])

    else:
        ret_array = ArrayDouble(np.empty((_s_sizeup, _ncols)))
        with parallel_config(backend="threading", n_jobs=_ncols, return_as="generator"):
            dat_list: list[np.ndarray] = Parallel()(
                delayed(_resample_empirical_margins_vector)(
                    _dist_parms, _s_sizeup, nthreads, _rng1i, _rng2i
                )
                for _rng1i, _rng2i in zip(
                    _rng1.spawn(_ncols), _rng2.spawn(_ncols), strict=True
                )
            )

        for _i in range(_ncols):
            ret_array[:, _i] = np.concatenate(dat_list[_i])

        return ret_array[:_ssz]  # type: ignore


def _resample_empirical_margins_vector(
    _parms: EmpiricalMarginData,
    _size: int,
    _nthreads: int,
    _rng1: Generator,
    _rng2: Generator,
    /,
) -> NDArray[np.float64]:
    """Generate draws on the empirical margin distribution."""
    _sub_sz = int(_size / _nthreads)

    dat_list = Parallel(backend="threading", n_jobs=_nthreads, return_as="generator")(
        delayed(_mgn_resampler)(_parms, _sub_sz, _rng1i, _rng2i)
        for _rng1i, _rng2i in zip(
            _rng1.spawn(_nthreads), _rng2.spawn(_nthreads), strict=True
        )
    )

    return np.vstack(list(dat_list))


def _mgn_resampler(
    _p: EmpiricalMarginData, _sz: int, _r1: Generator, _r2: Generator, /
) -> NDArray[np.float64]:
    """Generate draws on the empirical margin distribution."""
    return (
        _r1.choice(
            _p.average_gross_margins, p=(_w := _p.firm_counts) / _w.sum(), size=_sz
        )
        + _r2.standard_normal(size=_sz) * _p.bandwidth
    )


def _beta_located(
    _mu: float | ArrayDouble | ArrayFloat, _sigma: float | ArrayDouble | ArrayFloat, /
) -> ArrayFloat:
    """
    Given mean and stddev, return shape parameters (α, β) for corresponding Beta distribution.

    Solve the first two moments of the standard Beta to get the shape parameters.

    Parameters
    ----------
    _mu
        mean
    _sigma
        standardd deviation

    Returns
    -------
        shape parameters for Beta distribution

    """  # noqa: RUF002
    _mul = -1 + _mu * (1 - _mu) / (_sigma**2)
    return ArrayFloat([_mu * _mul, (1 - _mu) * _mul])  # type: ignore


def beta_located_bound(
    _dist_parms: ArrayDouble | ArrayFloat, /, *, frac: float = 0.05
) -> ArrayFloat:
    R"""
    Return shape parameters (α, β), location, and scale for a non-standard beta, given mean, stddev, and range.

    Note, however, that we slightly expand the range here to
    :math:`\left[\max, \min\right] = \left[\mathrm{floor}(\min / 0.1) * 0.1, \mathrm{ceil}(\max / 0.1 ) * 0.1\right]`.
    Recover the r.v.s as :math:`\min + (\max - \min) \cdot \symup{Β}(α, β)`,
    where :math:`α` and :math:`β` are the values returned here, being calculated from the specified mean (:math:`\mu`),
    standard deviation (:math:`\sigma`), :math:`\min`, and :math:`\max`. [#beta]_

    Parameters
    ----------
    _dist_parms
        vector of :math:`\mu`, :math:`\sigma`, :math:`\min`, and :math:`\max` values

    Returns
    -------
        shape parameters for Beta distribution

    Notes
    -----
    For example, ``beta_located_bound(np.array([0.5, 0.2, 0.1, 0.9]))``. Note, with a high variance
    (:math:`\sigma^2`) or tight range, the relative frequency of extreme values exceeds those in
    the middle of the range, which is atypical of observed margins. Alternatively, set the min and max
    to np.nan, in which case the range of margins is determined by the (shape paramters derived from)
    the mean and standard deviation.

    References
    ----------
    .. [#beta] NIST, Beta Distribution. https://www.itl.nist.gov/div898/handbook/eda/section3/eda366h.htm
    """  # noqa: RUF002
    _bmu, _bsigma, _bmin, _bmax = _dist_parms

    _bmin = _bmin if np.isnan(_bmin) else np.floor(_bmin / frac) * frac
    _bmax = _bmax if np.isnan(_bmax) else np.ceil(_bmax / frac) * frac
    _bscale = _bmax - _bmin
    # return 4-parameter calibration: α, β, loc, scale  # noqa: RUF003
    return ArrayFloat(
        (*_beta_located(_bmu, _bsigma), 0, 1)
        if np.isnan(_dist_parms[2:]).any or np.array_equal(_dist_parms[2:], [0, 1])
        else (
            *_beta_located((_bmu - _bmin) / _bscale, _bsigma / _bscale),
            _bmin,
            _bscale,
        )
    )
