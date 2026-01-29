"""Methods to generate data for analyzing merger enforcement policy."""

from __future__ import annotations

from itertools import starmap
from typing import TYPE_CHECKING, TypedDict

import numpy as np
from attrs import Attribute, Converter, define, field, validators
from joblib import Parallel, delayed, parallel_config  # type: ignore
from numpy.random import SeedSequence

if TYPE_CHECKING:
    from ruamel import yaml

    from ..core import MGThresholds

from .. import NTHREADS, PKG_NAME, VERSION, RECForm, this_yaml, yaml_rt_mapper, zipfile
from . import (
    SUBSAMPLE_SIZE,
    INVResolution,  # noqa: F401
    MarketsData,
    MarketShareSpec,
    PCMDistribution,
    PCMRestriction,
    PCMSpec,
    PriceSpec,
    SeedSequenceData,
    SHRDistribution,
    SSZConstant,
    UPPTestRegime,
    UPPTestsCounts,
)
from .data_generation_functions import (
    diversion_ratios_builder,
    market_share_sampler,
    prices_sampler,
)
from .upp_tests import compute_upp_test_counts

__version__ = VERSION


class SamplingFunctionKWArgs(TypedDict, total=False):
    """Keyword arguments of sampling methods defined below."""

    sample_size: int
    """number of draws to generate"""

    seed_data: SeedSequenceData | None
    """seed data to ensure independent and replicable draws"""

    nthreads: int
    """number of parallel threads to use"""


def _seed_data_conv(_v: SeedSequenceData | None, _i: MarketSample) -> SeedSequenceData:
    if isinstance(_v, SeedSequenceData):
        return _v

    _shr_seed, _pcm_seed = (
        _v[:2] if _v else tuple(SeedSequence(pool_size=8) for _ in range(2))
    )

    _uniform_share_distribution_flag = _i.share_spec.dist_type == SHRDistribution.UNI
    _fct_seed = (
        None
        if _i.share_spec.dist_type == SHRDistribution.UNI
        else (_v[2] if _v else SeedSequence(pool_size=8))
    )

    _random_price_variation_flag = _i.price_spec == PriceSpec.RND
    if not _random_price_variation_flag:
        _pri_seed = None
    elif not _v:
        _pri_seed = SeedSequence(pool_size=8)
    else:
        _pri_seed = _v[2] if _uniform_share_distribution_flag else _v[3]

    _hsr_test_random_flag = _i.hsr_filing_test_type.name.startswith("HSR_RND")
    if not _hsr_test_random_flag:
        _hft_seed = None
    elif not _v:
        _hft_seed = SeedSequence(pool_size=8)
    else:
        _idx = 2
        if _random_price_variation_flag:
            _idx += 1
        if not _uniform_share_distribution_flag:
            _idx += 1
        _hft_seed = _v[_idx]

    return SeedSequenceData(
        share=_shr_seed,
        pcm=_pcm_seed,
        fcounts=_fct_seed,
        price=_pri_seed,
        hsr_filing_test=_hft_seed,
    )


def _hsr_constant_converter(_v: SSZConstant, _i: MarketSample) -> SSZConstant:
    return (
        SSZConstant.HSR_TEN_UNI
        if _i.share_spec.dist_type == SHRDistribution.UNI and _v == SSZConstant.HSR_TEN
        else _v
    )


@this_yaml.register_class
@define(kw_only=True)
class MarketSample:
    """Parameter specification for market data generation."""

    share_spec: MarketShareSpec = field(
        default=MarketShareSpec(SHRDistribution.UNI),
        validator=validators.instance_of(MarketShareSpec),
    )
    """Market-share specification, see :class:`MarketShareSpec`"""

    pcm_spec: PCMSpec = field(
        default=PCMSpec(PCMDistribution.UNI), validator=validators.instance_of(PCMSpec)
    )
    """Margin specification, see :class:`PCMSpec`"""

    @pcm_spec.validator
    def _psv(self, _a: Attribute[PCMSpec], _v: PCMSpec, /) -> None:
        if (
            self.share_spec.recapture_form == RECForm.FIXED
            and _v.pcm_restriction == PCMRestriction.MNL
        ):
            raise ValueError(
                f'Specification of "PCMSpec.pcm_restriction", as {PCMRestriction.MNL!r} '
                f'requires that "MarketShareSpec.recapture_form" be {RECForm.INOUT!r} '
                f"or {RECForm.OUTIN!r}, not {RECForm.FIXED!r} as presently specified"
            )

    price_spec: PriceSpec = field(
        default=PriceSpec.SYM, validator=validators.instance_of(PriceSpec)
    )
    """Price specification, see :class:`PriceSpec`"""

    hsr_filing_test_type: SSZConstant = field(
        default=SSZConstant.ONE,
        converter=Converter(_hsr_constant_converter, takes_self=True),  # type: ignore
        validator=validators.instance_of(SSZConstant),
    )
    """Method for modeling HSR filing thresholds, see :class:`SSZConstant`"""

    @hsr_filing_test_type.validator
    def _hsfvt(self, _a: Attribute[SSZConstant], _v: SSZConstant, /) -> None:
        if (
            self.hsr_filing_test_type == SSZConstant.HSR_NTH
            or self.hsr_filing_test_type.name.startswith("HSR_RND")
        ) and self.share_spec.dist_type == SHRDistribution.UNI:
            raise ValueError(
                f'Specification of "SSZConstant", as {SSZConstant.HSR_NTH!r} '
                f"with market shares having uniform distribution is infeasible. "
                f"With uniformly distributed markets shares, share and prices are "
                f"defined for the merging firms only, so no n-th firm revenues can "
                f"be computed for implementing this form of HSR filing test."
            )

    sample_size: int = field(default=10**6, validator=validators.instance_of(int))
    """number of draws to simulate"""

    seed_data: SeedSequenceData = field(
        converter=Converter(_seed_data_conv, takes_self=True)  # type: ignore
    )
    """sequence of SeedSequences to ensure replicable data generation with
    appropriately independent random streams
    """

    @seed_data.default
    def _dsd(self) -> SeedSequenceData | None:
        return _seed_data_conv(None, self)

    @seed_data.validator
    def _sdv(
        _i: MarketSample, _a: Attribute[SeedSequenceData], _v: SeedSequenceData, /
    ) -> None:
        if _i.share_spec.dist_type == SHRDistribution.UNI and _v.fcounts:
            raise ValueError(
                "Attribute, seed_data.fcounts is ignored as irrelevant when "
                "market shares are drawn with Uniform distribution. "
                "Set seed_data.fcounts to None and retry."
            )

        if _i.price_spec != PriceSpec.RND and _v.price is not None:
            raise ValueError(
                "Attribute, seed_data.price is ignored as irrelevant unless "
                "prices are asymmetric and uncorrelated and price-cost margins "
                "are also not symmetric. Set seed_data.price to None and retry."
            )
        elif _i.price_spec == PriceSpec.RND and _v.price is None:
            raise ValueError(
                "Attribute, seed_data.price is required when prices are generated "
                "from random draws. Set seed_data.price and retry."
            )

        if (
            not _i.hsr_filing_test_type.name.startswith("HSR_RND")
            and _v.hsr_filing_test is not None
        ):
            raise ValueError(
                "Attribute, seed_data.price is ignored as irrelevant unless "
                "prices are asymmetric and uncorrelated and price-cost margins "
                "are also not symmetric. Set seed_data.price to None and retry."
            )
        elif (
            _i.hsr_filing_test_type.name.startswith("HSR_RND")
            and _v.hsr_filing_test is None
        ):
            raise ValueError(
                "Attribute, seed_data.hsr_filing_test is required when HSR filing "
                "test vectors are drawn from (Beta or uniform) distributions. Set "
                "seed_data.hsr_filing_test and retry."
            )

    nthreads: int = field(default=NTHREADS, validator=validators.instance_of(int))
    """number of parallel threads to use"""

    dataset: MarketsData | None = field(default=None, init=False)

    enf_counts: UPPTestsCounts | None = field(default=None, init=False)

    def _markets_sampler(
        self,
        /,
        *,
        sample_size: int | None = None,
        seed_data: SeedSequenceData | None = None,
        nthreads: int | None = None,
    ) -> MarketsData:
        """
        Generate share, diversion ratio, price, and margin data for MarketSpec.

        The optional keyword arguments are present to allow parallel generation of
        enforcement counts over a given sample size without saving the generated data.
        see :attr:`SamplingFunctionKWArgs` for description of keyword parameters

        Returns
        -------
        Merging firms' shares, margins, etc. for each hypothetical  merger
        in the sample

        """
        sample_size = sample_size or self.sample_size
        seed_data = seed_data or self.seed_data
        nthreads = nthreads or self.nthreads

        # Scale up sample size to offset discards based on specified criteria
        shr_sample_size = sample_size * self.hsr_filing_test_type
        shr_sample_size *= (
            (
                SSZConstant.MNL_DEP_UNI
                if self.share_spec.dist_type == SHRDistribution.UNI
                else SSZConstant.MNL_DEP
            )
            if self.pcm_spec.pcm_restriction == PCMRestriction.MNL
            else 1
        )
        shr_sample_size = int(shr_sample_size)

        # Generate share data
        mktshr_data = market_share_sampler(
            self.share_spec, shr_sample_size, seed_data, nthreads
        )
        # Generate merging-firm price and PCM data
        margin_data, price_data = prices_sampler(
            self.share_spec,
            self.pcm_spec,
            self.price_spec,
            self.hsr_filing_test_type,
            mktshr_data,
            seed_data,
            nthreads,
        )

        mktshr_array_ = mktshr_data.mktshr_array
        fcounts_ = mktshr_data.fcounts
        aggregate_purchase_prob_ = mktshr_data.aggregate_purchase_prob
        nth_firm_share_ = mktshr_data.nth_firm_share

        pcm_array_ = margin_data.pcm_array

        price_array_ = price_data.price_array

        if shr_sample_size > sample_size:
            mnl_test_rows = margin_data.mnl_test * price_data.hsr_filing_test

            mktshr_array_ = mktshr_array_[mnl_test_rows][:sample_size]
            pcm_array_ = margin_data.pcm_array[mnl_test_rows][:sample_size]
            price_array_ = price_data.price_array[mnl_test_rows][:sample_size]
            aggregate_purchase_prob_ = aggregate_purchase_prob_[mnl_test_rows][
                :sample_size
            ]
            fcounts_, nth_firm_share_ = (
                _v
                if self.share_spec.dist_type == SHRDistribution.UNI
                else _v[mnl_test_rows][:sample_size]
                for _v in (fcounts_, nth_firm_share_)
            )

            del mnl_test_rows

        # Calculate diversion ratios
        divratio_array = diversion_ratios_builder(
            self.share_spec.recapture_form,
            self.share_spec.recapture_rate,
            mktshr_array_,
            aggregate_purchase_prob_,
        )

        return MarketsData(
            mktshr_array_[:, :2],
            pcm_array_,
            price_array_,
            divratio_array,
            (
                _dh := np.einsum(
                    "ij,ij->i", mktshr_array_[:, :2], mktshr_array_[:, :2][:, ::-1]
                )[:, None]
            ),
            aggregate_purchase_prob_,
            fcounts_,
            nth_firm_share_,
            (
                np.array([], float)
                if self.share_spec.dist_type == SHRDistribution.UNI
                else (
                    np.einsum(  # pre-merger HHI
                        "ij,ij->i", mktshr_array_, mktshr_array_
                    )[:, None]
                    + _dh
                )
            ),
        )

    def generate_sample(self, /) -> None:
        """Populate :attr:`data` with generated data.

        Returns
        -------
        None

        """
        object.__setattr__(self, "dataset", self._markets_sampler())

    def _sim_enf_cnts(
        self,
        _upp_test_parms: MGThresholds,
        _sim_test_regime: UPPTestRegime,
        /,
        *,
        seed_data: SeedSequenceData,
        sample_size: int = 10**6,
        nthreads: int = NTHREADS,
    ) -> UPPTestsCounts:
        """Generate market data and compute UPP test counts on same.

        Parameters
        ----------
        _upp_test_parms
            Guidelines thresholds for testing UPP and related statistics

        _sim_test_regime
            Configuration to use for testing; UPPTestsRegime object
            specifying whether investigation results in enforcement, clearance,
            or both; and aggregation methods used for GUPPI and diversion ratio
            measures

        sample_size
            Number of draws to generate

        seed_data
            List of seed sequences, to assure independent samples in each thread

        nthreads
            Number of parallel processes to use

        Returns
        -------
            UPPTestCounts object with  of test counts by firm count, ΔHHI and concentration zone

        """
        market_data_sample = self._markets_sampler(
            sample_size=sample_size, seed_data=seed_data, nthreads=nthreads
        )

        upp_test_arrays: UPPTestsCounts = compute_upp_test_counts(
            market_data_sample, _upp_test_parms, _sim_test_regime
        )

        return upp_test_arrays

    def _sim_enf_cnts_ll(
        self, _enf_parm_vec: MGThresholds, _sim_test_regime: UPPTestRegime, /
    ) -> UPPTestsCounts:
        """Parallelize data-generation and testing.

        The parameters `_sim_enf_cnts_kwargs` are passed unaltered to
        the parent function, `sim_enf_cnts()`, except that, if provided,
        `seed_data` is used to spawn a seed sequence for each thread,
        to assure independent samples in each thread, and `nthreads` defines
        the number of parallel processes used. The number of draws in
        each thread may be tuned, by trial and error, to the amount of
        memory (RAM) available.

        Parameters
        ----------
        _enf_parm_vec
            Guidelines thresholds to test against

        _sim_test_regime
            Configuration to use for testing

        Returns
        -------
            Arrays of enforcement counts or clearance counts by firm count,
            ΔHHI and concentration zone

        """
        sample_sz = self.sample_size
        subsample_sz = SUBSAMPLE_SIZE
        iter_count = (sample_sz / subsample_sz).__ceil__()
        thread_count = self.nthreads

        if (
            self.share_spec.recapture_form != RECForm.OUTIN
            and self.share_spec.recapture_rate != _enf_parm_vec.rec
        ):
            raise ValueError(
                "{} {} {}".format(
                    f"Recapture rate from market sample spec, {self.share_spec.recapture_rate}",
                    f"must match the value, {_enf_parm_vec.rec}",
                    "the guidelines thresholds vector.",
                )
            )

        # The expression below does the following:
        #  1. Spawn inter_count number of seed sequences for each seed
        #     (attribute) in seed_data
        #  2. Zip the i-th seeds across the spawns into a generator over
        #     the spawns
        #  3. Map the SeedSequenceData constructor over each sequence of i-th
        #     spawns to get iter_count seed sequences used to seed the iterations
        rng_seed_data = list(
            starmap(
                SeedSequenceData,
                zip(
                    *[
                        _s.spawn(iter_count) if _s else [None] * iter_count
                        for _s in (
                            getattr(self.seed_data, _a.name)
                            for _a in self.seed_data.__attrs_attrs__
                        )
                    ],
                    strict=True,
                ),
            )
        )

        sim_enf_cnts_kwargs: SamplingFunctionKWArgs = SamplingFunctionKWArgs({
            "sample_size": subsample_sz,
            "nthreads": thread_count,
        })

        with parallel_config(
            backend="threading",
            n_jobs=min(thread_count, iter_count),
            return_as="generator",
        ):
            res_list = Parallel()(
                delayed(self._sim_enf_cnts)(
                    _enf_parm_vec,
                    _sim_test_regime,
                    **sim_enf_cnts_kwargs,
                    seed_data=_rng_seed_data_ch,
                )
                for _rng_seed_data_ch in rng_seed_data
            )

        res_list_stacks = [
            np.stack([getattr(_j, _k) for _j in res_list])
            for _k in ("ByFirmCount", "ByDelta", "ByHHIandDelta")
        ]

        upp_test_results = UPPTestsCounts(*[
            (
                []
                if not _g.any()
                else np.hstack((
                    _g[0, :, :_h],
                    np.einsum("ijk->jk", _g[:, :, _h:], dtype=int),
                ))
            )
            for _g, _h in zip(res_list_stacks, [1, 1, 3], strict=True)
        ])
        del res_list, res_list_stacks

        return upp_test_results

    def estimate_enf_counts(
        self, _enf_parm_vec: MGThresholds, _upp_test_regime: UPPTestRegime, /
    ) -> None:
        """Populate :attr:`enf_counts` with estimated UPP test counts.

        If the :attr:`dataset` attribute is not None, the counts are
        computed on the :attr:`dataset` attribute. Otherwise, enforcement counts
        are computed in parallel on data generated on the fly. Note here that if
        the sample size is not an even multiple of SUBSAMPLE_SIZE,
        the sample on which enforcement counts are computed will be larger than
        the specified sample size, by up to SUBSAMPLE_SIZE draws less 1.

        Parameters
        ----------
        _enf_parm_vec
            Threshold values for various Guidelines criteria

        _upp_test_regime
            Specifies whether to analyze enforcement, clearance, or both
            and the GUPPI and diversion ratio aggregators employed, with
            default being to analyze enforcement based on the maximum
            merging-firm GUPPI and maximum diversion ratio between the
            merging firms

        Returns
        -------
        None

        """
        if self.dataset is None:
            self.enf_counts = self._sim_enf_cnts_ll(_enf_parm_vec, _upp_test_regime)
        else:
            self.enf_counts = compute_upp_test_counts(
                self.dataset, _enf_parm_vec, _upp_test_regime
            )

    def to_archive(
        self, zip_: zipfile.ZipFile, _subdir: str = "", /, *, save_dataset: bool = False
    ) -> None:
        """Serialize market sample to Zip archive."""
        zpath = zipfile.Path(zip_, at=_subdir)
        name_root = f"{PKG_NAME}_market_sample"

        with (zpath / f"{name_root}.yaml").open("w") as _yfh:
            this_yaml.dump(self, _yfh)

        if save_dataset:
            if self.dataset is None and self.enf_counts is None:
                raise ValueError(
                    "No dataset and/or enforcement counts available for saving. "
                    "Generate some data or set save_dataset to False to proceed."
                )

            else:
                if self.dataset is not None:
                    with (zpath / f"{name_root}_dataset.h5").open("wb") as _hfh:
                        _hfh.write(self.dataset.to_h5bin())

                if self.enf_counts is not None:
                    with (zpath / f"{name_root}_enf_counts.yaml").open("w") as _yfh:
                        this_yaml.dump(self.enf_counts, _yfh)

    @staticmethod
    def from_archive(
        zip_: zipfile.ZipFile, _subdir: str = "", /, *, restore_dataset: bool = False
    ) -> MarketSample:
        """Deserialize market sample from Zip archive."""
        zpath = zipfile.Path(zip_, at=_subdir)
        name_root = f"{PKG_NAME}_market_sample"

        market_sample_: MarketSample = this_yaml.load(
            (zpath / f"{name_root}.yaml").read_text()
        )

        if restore_dataset:
            _dt = (_dp := zpath / f"{name_root}_dataset.h5").is_file()
            _et = (_ep := zpath / f"{name_root}_enf_counts.yaml").is_file()
            if not (_dt or _et):
                raise ValueError(
                    "Archive has no sample data to restore. "
                    "Delete second argument, or set it False, and rerun."
                )
            else:
                if _dt:
                    with _dp.open("rb") as _hfh:
                        object.__setattr__(
                            market_sample_, "dataset", MarketsData.from_h5f(_hfh)
                        )
                if _et:
                    object.__setattr__(
                        market_sample_, "enf_counts", this_yaml.load(_ep.read_text())
                    )
        return market_sample_

    @classmethod
    def to_yaml(
        cls, _r: yaml.representer.RoundTripRepresenter, _d: MarketSample
    ) -> yaml.MappingNode:
        """Serialize market sample to YAML representation."""
        retval: yaml.MappingNode = _r.represent_mapping(
            f"!{cls.__name__}",
            {
                _a.name: getattr(_d, _a.name)
                for _a in _d.__attrs_attrs__
                if _a.name not in {"dataset", "enf_counts"}
            },
        )
        return retval

    @classmethod
    def from_yaml(
        cls, _c: yaml.constructor.RoundTripConstructor, _n: yaml.MappingNode
    ) -> MarketSample:
        """Deserialize market sample from YAML representation."""
        return cls(**yaml_rt_mapper(_c, _n))
