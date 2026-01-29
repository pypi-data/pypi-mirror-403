"""Defines constants, specifications and containers for industry data generation and testing."""

from __future__ import annotations

import enum
import io
from collections.abc import Sequence
from operator import attrgetter
from typing import IO, TYPE_CHECKING

import h5py  # type: ignore
import hdf5plugin
import numpy as np
from attrs import Attribute, Converter, cmp_using, field, frozen

if TYPE_CHECKING:
    from numpy.random import SeedSequence

    from .. import zipfile

from .. import (
    DEFAULT_REC,
    EMPTY_ARRAYDOUBLE,
    EMPTY_ARRAYUINT8,
    VERSION,
    ArrayBIGINT,
    ArrayBoolean,
    ArrayDouble,
    ArrayFloat,
    ArrayINT,
    ArrayUINT8,
    Enameled,
    RECForm,
    UPPAggrSelector,
    this_yaml,
    yamlize_attrs,
)
from ..core import DEFAULT_BETA_DIST_PARMS, DEFAULT_DIST_PARMS, EmpiricalMarginData
from ..core.empirical_margin_distribution import margin_data_builder

__version__ = VERSION

DEFAULT_DIR_COND_DIST_PARMS = ArrayFloat([2.5, 2.5, 1.0])
DEFAULT_FCOUNT_WTS: ArrayFloat = ArrayFloat((_nr := np.arange(6, 0, -1)) / _nr.sum())
HSR_RATIO = 10
"""Ratio of large-firm to small-firm revenues, for HSR filing test.

See, https://www.ftc.gov/enforcement/premerger-notification-program/.

The HSR filing thresholds, of $10 million and $100 million in
part (a) Filing of
15 U.S.C. 18a. Premerger notification and waiting period
under (2)(B)(ii)(I) reflect a 10-to-1 revenue ratio
that is unchanged under annual revisions required by law.
Thus, a simple form of the HSR filing test would impose a 10-to-1
ratio restriction (max.-to-min.) on the merging firms' revenues. This
version of the filing test is implemented by specifying `hsr_filing_test_type`
as :attr:`SSZConstant.HSR_TEN`.

Note, however, the filing test does not *require* that
the larger merging firm be ten times the size of the smaller merging firm.
Indeed, it is also not sufficient for meeting the HSR filing test that
one merging firm's revenues are no less than ten times the others ---
a proposed merger does not require a filing if the larger firm's revenue is
$101 million, adjusted for inflation, and the smaller firm's revenue is $9 million, adjusted
for inflation, and none of the other filing requirements are met, despite the
ratio of merging firms' revenues being greater than 10-to-1.
On the other hand, if both firms are of approximately the same size and each has revenues
greater than $100 million, adjusted for inflation, the proposed merger meets
the HSR filing test despite the ratio of the merging firm's revenues being
1-to-1.

Accordingly, this package supports an alternate assumption regarding the filing test,
as follows: assume that the n-th firm has annual revenues of $10 million. Then,
a proposed merger meets the annual revenue test if the smaller merging firm's
revenue relative to the n-th firm's is no less than 1, and the larger firm's
revenue relative to the n-th firm's is no less than 10. This version of
the filing test is implemented by specifying `hsr_filing_test_type`
as :attr:`mergeron.gen.SSZConstant.HSR_NTH`.
"""

HSR_BETA_PARMS = globals().get("HSR_BETA_PARMS", (40.0, 1130.0))
"""
The version of the HSR filing test parameterized by :attr:`SSZConstant.HSR_NTH` is less
restrictive than that of :attr:`SSZConstant.HSR_TEN`, but it is still
restrictive of the market structures (pre- and post-merger concentration levels)
observable in generated data. To lift this restriction, we add version parameterized by
:attr:`SSZConstant.HSR_RNDB` and :attr:`SSZConstant.HSR_RNDU`. In this version, we draw
a test vector of revenues from a Beta distribution with the parameters given here
or, alternatively, the uniform distribution between 0 and 1, and maintain that
the potential merger in a given draw requires a HSR filing if the smaller merging firm's revenue
is no less than the corresponding value in the test vector and the
larger merging firm's share is no less than ten times the corresponding value in
the test vector.

The parameters given here are derived for generating a Beta distribution with mean of 3% and
standard deviation of 0.5%, and rounding the results to the nearest tens. At these parameters,
the smaller merging firm's share in virtually all (more than 99.5%) of mergers assumed to
require a HSR filing will exceed 2.5% and the combined share will exceed 26.5%, with
the change in concentration exceeding 133 points.
"""

SUBSAMPLE_SIZE = 10**6
"""Subsample size for parallelization."""


@frozen
class SeedSequenceData:
    """Seed sequence values for shares, margins, and, optionally, firm-counts and prices."""

    share: SeedSequence = field(eq=attrgetter("state"))
    pcm: SeedSequence = field(eq=attrgetter("state"))
    fcounts: SeedSequence | None = field(eq=lambda x: x if x is None else x.state)
    price: SeedSequence | None = field(eq=lambda x: x if x is None else x.state)
    hsr_filing_test: SeedSequence | None = field(
        eq=lambda x: x if x is None else x.state
    )


@this_yaml.register_class
@enum.unique
class PriceSpec(str, Enameled):
    """Price specification.

    The structure of prices, in terms of shares, if any.
    """

    CSY = "market-wide cost-symmetry"
    NEG = "negative share-correlation"
    POS = "positive share-correlation"
    RND = "random, in steps"
    SYM = None


@this_yaml.register_class
@enum.unique
class PriceCostStructure(str, Enameled):
    """Price-cost structure."""

    SYM = "symmetric"
    """Uniform price-cost margins."""

    CST = "inferred from costs and margins"
    NEG = "negatively correlated with share"
    POS = "positively correlated with share"
    RND = "random, in steps"


@this_yaml.register_class
@enum.unique
class SHRDistribution(str, Enameled):
    """Market share distributions."""

    UNI = "Uniform"
    R"""Uniform distribution over :math:`s_1 + s_2 \leqslant 1`"""

    DIR_FLAT = "Flat Dirichlet"
    """Shape parameter for all merging-firm-shares is unity (1)"""

    DIR_FLAT_CONSTR = "Flat Dirichlet - Constrained"
    """Impose minimum probability weight on each firm-count

    Only firm-counts with probability weight of 3% or more
    are included for data generation.
    """

    DIR_ASYM = "Asymmetric Dirichlet"
    """Share distribution for merging-firm shares has a higher peak share

    By default, shape parameter for merging-firm-share is 2.5, and
    1.0 for all others. Defining, :attr:`.MarketShareSpec.dist_parms`
    as a vector of shape parameters with length matching
    that of :attr:`.MarketShareSpec.dist_parms` allows flexible specification
    of Dirichlet-distributed share-data generation.
    """

    DIR_COND = "Conditional Dirichlet"
    """Shape parameters for non-merging firms is proportional

    Shape parameters for merging-firm-share are given as the first two
    elements of :attr:`.MarketShareSpec.dist_parms`; the shape parameters
    for the remaining firms' shares are equiproportional and sum to the
    third element of :attr:`.MarketShareSpec.dist_parms`. See,
    Balakrishnan [#balakrishnan2006]_ (p. 25).

    .. [#balakrishnan2006] Balakrishnan, V. (2014). Continuous Multivariate Distributions.
      Wiley StatsRef: Statistics Reference Online

    """


def _fc_wts_conv(
    _v: Sequence[float | int] | ArrayDouble | ArrayINT | None, _i: MarketShareSpec
) -> ArrayFloat | None:
    if _i.dist_type == SHRDistribution.UNI:
        return None
    elif _v is None or len(_v) == 0 or np.array_equal(_v, DEFAULT_FCOUNT_WTS):
        return DEFAULT_FCOUNT_WTS
    else:
        return ArrayFloat(
            _tv if (_tv := np.asarray(_v, float)).sum() == 1 else _tv / _tv.sum()
        )


def _shr_dp_conv(
    _v: Sequence[float] | ArrayFloat | None, _i: MarketShareSpec
) -> ArrayFloat:
    retval = np.array([], float)
    if _v is None or len(_v) == 0 or np.array_equal(_v, DEFAULT_DIST_PARMS):
        if _i.dist_type == SHRDistribution.UNI:
            return DEFAULT_DIST_PARMS
        else:
            fc_max = 1 + (
                len(DEFAULT_FCOUNT_WTS)
                if _i.firm_counts_weights is None
                else len(_i.firm_counts_weights)
            )

            match _i.dist_type:
                case SHRDistribution.DIR_FLAT | SHRDistribution.DIR_FLAT_CONSTR:
                    retval = np.ones(fc_max)
                case SHRDistribution.DIR_ASYM:
                    retval = np.array([2.0] * 6 + [1.5] * 5 + [1.25] * fc_max)
                case SHRDistribution.DIR_COND:
                    # alpha-value for merging firms; alpha for non-merging firms
                    # computed as in Balakrishnan, 2005, p. 25
                    retval = DEFAULT_DIR_COND_DIST_PARMS
                case _ if isinstance(_i.dist_type, SHRDistribution):
                    raise ValueError(
                        f"No default defined for market share distribution, {_i.dist_type!r}"
                    )
                case _:
                    raise ValueError(
                        f"Unsupported distribution for market share generation, {_i.dist_type!r}"
                    )
    elif isinstance(_v, Sequence | np.ndarray):
        retval = np.asarray(_v, float)
    else:
        raise ValueError(
            f"Input, {_v!r} has invalid type. Must be None, Sequence of floats, or Numpy ndarray."
        )

    return ArrayFloat(retval)


@frozen
class MarketShareSpec:
    """Market share specification.

    Choosing a Dirichlet-type distribution allows pooling data generated for
    markets with varying numbers of firms, specifying by a vector of firm-count
    weights with the first element giving the relative proportion of two-firm markets
    and on down the line. Choosing uniformly distributed shares allows generation of
    data for markets with unspecified numbers of firms.

    Notes
    -----
    If :attr:`.dist_type` == :attr:`.SHRDistribution.UNI`, it is then infeasible that
    :attr:`.recapture_form` == :attr:`mergeron.RECForm.OUTIN`.
    In other words, recapture rates cannot be estimated using
    outside-good choice probabilities if the distribution of markets over firm-counts
    is unspecified.

    We impose the further restriction that if shares have a Dirichlet distribution,
    then recapture rates cannot be fixed (:attr:`mergeron.RECForm.FIXED`). As the
    generated data are sufficient for computing exact recapture rates for each firm and
    exact recapture rates are not fixed, the above restriction enforces internal
    consistency.

    Fixed recapture rates are inconsistent with theory, unless demand and prices are symmetric,
    but are supported here to allow comparison with external results.
    """

    dist_type: SHRDistribution = field(kw_only=False)
    """See :class:`SHRDistribution`"""

    firm_counts_weights: ArrayFloat | None = field(
        kw_only=True,
        eq=cmp_using(eq=np.array_equal),
        converter=Converter(_fc_wts_conv, takes_self=True),  # type: ignore
    )
    """Relative or absolute frequencies of pre-merger firm counts

    Defaults to :attr:`DEFAULT_FCOUNT_WTS`, which specifies pre-merger
    firm-counts of 2 to 7 with weights in descending order from 6 to 1.

    ALERT: Firm-count weights are irrelevant when the merging firms' shares are specified
    to have uniform distribution; therefore this attribute is forced to None if
    :attr:`.dist_type` == :attr:`.SHRDistribution.UNI`.
    """

    @firm_counts_weights.default
    def _fcwd(_i: MarketShareSpec) -> ArrayFloat | None:
        return _fc_wts_conv(None, _i)

    @firm_counts_weights.validator
    def _fcv(_i: MarketShareSpec, _a: Attribute[ArrayFloat], _v: ArrayFloat) -> None:
        if _i.dist_type != SHRDistribution.UNI and not len(_v):
            raise ValueError(
                f"Attribute, {'"firm_counts_weights"'} must be populated if the share distribution is "
                "other than uniform distribution."
            )

    dist_parms: ArrayFloat | ArrayDouble = field(
        kw_only=True,
        converter=Converter(_shr_dp_conv, takes_self=True),  # type: ignore
        eq=cmp_using(eq=np.array_equal),
    )
    """Parameters for tailoring market-share distribution

    For Uniform distribution, bounds of the distribution; defaults to `(0, 1)`;
    for Dirichlet-type distributions, a vector of shape parameters of length
    equal to 1 plus the length of firm-count weights below; defaults depend on
    type of Dirichlet-distribution specified.
    """

    @dist_parms.default
    def _dpd(_i: MarketShareSpec) -> ArrayFloat:
        # converters run after defaults, and we
        # avoid redundancy and confusion here
        return _shr_dp_conv(None, _i)

    @dist_parms.validator
    def _dpv(_i: MarketShareSpec, _a: Attribute[ArrayFloat], _v: ArrayFloat) -> None:
        if (
            _i.firm_counts_weights is not None
            and len(_v) < (1 + len(_i.firm_counts_weights))
            and _i.dist_type != SHRDistribution.DIR_COND
        ):
            print(_i)
            raise ValueError(
                "If specified, the number of distribution parameters must equal or "
                "exceed the maximum firm-count premerger, namely 1 plus"
                "the length of the vector specifying firm-count weights."
            )
        elif _i.dist_type == SHRDistribution.DIR_COND and len(_v) != len((
            "theta_1",
            "theta_2",
            "Theta",
        )):
            raise ValueError(
                f"Given number, {len(_v)} of parameters "
                f'for PCM with distribution, "{_i.dist_type}" is incorrect.'
            )

    lower_bound: float = field(kw_only=True, default=1e-2)
    """Restriction on market share draws.

    Minimum market share in each draw must be greater than this value (i.e., the
    lower bound in non-inclusive, or "open"). It is
    useful to set this value to 1% (say) when comparing intrinsic enforcement
    rates with observed rates as a limit on the precision of share estimates in
    actual merger investigations. For verifying enforcement rates computed by
    simulation versus those from closed-form expressions, the `lower_bound` for
    generated market shares should be set to 0. The default value is 0.0.

    Setting this threshold higher than 1% will have the undesirable result that
    the size of the market share array generated will be smaller length than
    the specified sample size.

    This threshold is not enforced when shares are drawn from the
    conditional Dirichlet distribution [#balakrishnan]_ specified in this package,
    in which the alpha parameters for generating the merging firms shares
    are [2.5, 2.5, 1.0], and the alpha parameters for generating
    the non-merging firms's shares are computed to sum to 1.0 and replace
    the final entry in the vector given above. The conditional Dirichlet distribution
    as implemented here is useful for maintaining that the distribution of
    merging-firm shares is not decreasing in the number of firms in the market, as with
    share generated using other forms of the Dirichlet distribution.

    .. [#balakrishnan] Balakrishnan, S. (2006). Continuous Multivariate Distributions. *In*
    John Wiley & Sons, Wiley StatsRef: Statistics Reference Online (2014).
    """

    recapture_form: RECForm = field(default=RECForm.INOUT)
    """See :class:`mergeron.RECForm`"""

    @recapture_form.validator
    def _rfv(_i: MarketShareSpec, _a: Attribute[RECForm], _v: RECForm) -> None:
        if _i.dist_type == SHRDistribution.UNI and _v == RECForm.OUTIN:
            raise ValueError(
                "Outside-good choice probabilities cannot be generated if the "
                "merging firms' market shares have uniform distribution over the "
                "3-dimensional simplex --- the shares of non-merging firms are "
                "indeterminate."
            )
        elif "DIR" in _i.dist_type.name and _v == RECForm.FIXED:
            raise ValueError(
                "Recapture rates cannot be held fixed for all firms when "
                "shares and diversion ratios of non-merging firms are drawn from "
                "Dirichlet distributions and, therefore, are known."
            )

    recapture_rate: float | None = field(kw_only=True)
    """A value between 0 and 1.

    :code:`None` if market share specification requires direct generation of
    outside good choice probabilities (:attr:`mergeron.RECForm.OUTIN`).

    The recapture rate is usually calibrated to the numbers-equivalent of the
    HHI threshold for the presumption of harm from unilateral competitive effects
    in published merger guidelines. Accordingly, the recapture rate rounded to
    the nearest 5% is:

    * 0.85, **7-to-6 merger from symmetry**; US Guidelines, 1992, 2023
    * 0.80, 5-to-4 merger from symmetry
    * 0.80, **5-to-4 merger to symmetry**; US Guidelines, 2010

    Highlighting indicates hypothetical mergers in the neighborhood of (the boundary of)
    the Guidelines presumption of harm. (In the EU Guidelines, concentration measures serve as
    screens for further investigation, rather than as the basis for presumptions of harm or
    presumptions no harm.)

    ALERT: If diversion ratios are estimated by specifying a choice probability for the
    outside good, the recapture rate is set to None, overriding any user-specified value.
    """

    @recapture_rate.default
    def _rrd(_i: MarketShareSpec) -> float | None:
        return None if _i.recapture_form == RECForm.OUTIN else DEFAULT_REC

    @recapture_rate.validator
    def _rrv(_i: MarketShareSpec, _a: Attribute[float], _v: float) -> None:
        if _v and not (0 < _v <= 1):
            raise ValueError("Recapture rate must lie in the interval, [0, 1).")


@this_yaml.register_class
@enum.unique
class PCMDistribution(str, Enameled):
    """Margin distributions."""

    UNI = "Uniform"
    BETA = "Beta"
    EMPR_U = "Damodaran margin data, uni-modal resampling"
    EMPR_M = "Damodaran margin data, multi-modal resampling"


@this_yaml.register_class
@enum.unique
class PCMRestriction(str, Enameled):
    """Restriction on generated Firm 2 margins."""

    IID = "independent and identically distributed (IID)"
    MNL = "Nash-Bertrand equilibrium with multinomial logit (MNL) demand"
    SYM = "symmetric"


def _pcm_dp_conv(
    _v: ArrayFloat | Sequence[float] | None, _i: PCMSpec
) -> ArrayFloat | ArrayDouble | EmpiricalMarginData:
    if (
        _v is None or isinstance(_v, EmpiricalMarginData)
    ) and _i.dist_type == PCMDistribution.EMPR_M:
        if isinstance(_v, EmpiricalMarginData):
            return _v
        return margin_data_builder()
    elif _v is None or len(_v) == 0 or np.array_equal(_v, DEFAULT_DIST_PARMS):
        match _i.dist_type:
            case PCMDistribution.BETA:
                return DEFAULT_BETA_DIST_PARMS
            case PCMDistribution.EMPR_U:
                return margin_data_builder().margin_stats
            case _:
                return DEFAULT_DIST_PARMS
    elif isinstance(_v, Sequence | np.ndarray):
        return ArrayFloat(np.array(_v, float) if isinstance(_v, Sequence) else _v)
    else:
        raise ValueError(
            f"Input, {_v!r} has invalid type. Must be None, sequence of floats,"
            "sequence of Numpy arrays, or Numpy ndarray."
        )


@frozen
class PCMSpec:
    """Price-cost margin (PCM) specification.

    If price-cost margins are specified as having Beta distribution,
    `dist_parms` is specified as a pair of positive, non-zero shape parameters of
    the standard Beta distribution. Specifying shape parameters :code:`np.array([1, 1])`
    is known equivalent to specifying uniform distribution over
    the interval :math:`[0, 1]`. If price-cost margins are specified as having
    Bounded-Beta distribution, `dist_parms` is specified as
    the tuple, (`mean`, `std deviation`, `min`, `max`), where `min` and `max`
    are lower- and upper-bounds respectively within the interval :math:`[0, 1]`.
    """

    dist_type: PCMDistribution = field()
    """See :class:`PCMDistribution`"""

    @dist_type.default
    def _dtd(_i: PCMSpec) -> PCMDistribution:
        return PCMDistribution.UNI

    dist_parms: ArrayFloat | ArrayDouble | EmpiricalMarginData = field(
        kw_only=True,
        eq=cmp_using(
            lambda _i, _j: (
                _i == _j
                if isinstance(_i, EmpiricalMarginData)
                else np.array_equal(_i, _j)
            )
        ),
        converter=Converter(_pcm_dp_conv, takes_self=True),  # type: ignore
    )
    """Parameter specification for tailoring PCM distribution

    For Uniform distribution, bounds of the distribution; defaults to `(0, 1)`;
    for Beta distribution, shape parameters, defaults to `(1, 1)`;
    for Bounded-Beta distribution, vector of (min, max, mean, std. deviation), non-optional;
    for Empirical distribution, the converter functions supplies a computed data structure
    """

    @dist_parms.default
    def _dpwd(_i: PCMSpec) -> ArrayDouble | ArrayFloat | EmpiricalMarginData:
        return _pcm_dp_conv(None, _i)

    @dist_parms.validator
    def _dpv(
        _i: PCMSpec,
        _a: Attribute[ArrayFloat | Sequence[ArrayDouble] | None],
        _v: ArrayFloat | Sequence[ArrayDouble] | None,
    ) -> None:
        if _i.dist_type.name.startswith("BETA"):
            if (
                _v is None
                or not hasattr(_v, "len")
                or (isinstance(_v, np.ndarray) and not any(_v.shape))
            ):
                pass
            elif np.array_equal(_v, DEFAULT_DIST_PARMS):
                raise ValueError(
                    f"The distribution parameters, {DEFAULT_DIST_PARMS!r} "
                    "are not valid with margin distribution, {_dist_type_pcm!r}"
                )
            elif (
                _i.dist_type == PCMDistribution.BETA and len(_v) != len(("a", "b"))
            ) or (
                _i.dist_type == PCMDistribution.EMPR_U
                and len(_v) != len(("mu", "sigma", "max", "min"))
            ):
                raise ValueError(
                    f"Given number, {len(_v)} of parameters "
                    f'for PCM with distribution, "{_i.dist_type}" is incorrect.'
                )

        elif _i.dist_type == PCMDistribution.EMPR_M and not isinstance(
            _v, EmpiricalMarginData
        ):
            raise ValueError(
                "Parameter input for empirical distribution must be structured as EmpiricalMarginData."
            )

    pcm_restriction: PCMRestriction = field(kw_only=True, default=PCMRestriction.IID)
    """See :class:`PCMRestriction`"""

    @pcm_restriction.validator
    def _prv(_i: PCMSpec, _a: Attribute[PCMRestriction], _v: PCMRestriction) -> None:
        if _v == PCMRestriction.MNL and _i.dist_type == PCMDistribution.EMPR_M:
            print(
                "NOTE: For consistency of generated Firm 2 margins with source data,",
                "respecify PCMSpec with pcm_restriction=PCMRestriction.IID.",
                sep="\n",
            )


@frozen
class PriceSpec_:
    """Defines the structure of prices.

    Also used to defines the structure of costs, when costs are not
    inferred from prices and margins but rather prices are defined
    by margins and the structure of costs.
    """

    price_structure: PriceCostStructure = field(default=PriceCostStructure.SYM)
    """See :class:`PriceStructure`"""

    cost_structure: PriceCostStructure | None = field(default=None)
    """Typically inferred from price structure and margins.

    However, when the price structure is defined to be derived by costs, i.e.,
    when `.price_structure` is specified as :attr:`PriceCostStructure.CST`, this
    field is used to specify the cost structure. This attribute cannot, of course,
    be assigned to :attr:`PriceCostStructure.CST`, which the validator ensures.
    """

    @cost_structure.validator
    def _cstv(
        _i: PriceSpec_,
        _a: Attribute[PriceCostStructure | None],
        _v: PriceCostStructure | None,
    ) -> None:
        if _v == PriceCostStructure.CST:
            raise ValueError(
                "PriceSpec.cost_structure cannot be assigned to PriceCostStructure.CST"
            )

    normalization: float = field(default=1.0)
    """Seldom needs to be other than 1.0.

    All analysis within this package is done in relative prices. Thus there is seldom
    reason to normalize prices or costs to a level other than 1.0.
    """

    step_count: int = field(default=5)
    """Number of distinct prices  or costs drawn.

    When prices are correlated with shares, or random within bounds, this
    attribute specifies the number of distinct prices or costs generated.
    """


@this_yaml.register_class
@enum.unique
class SSZConstant(float, Enameled):
    """
    Scale factors to offset sample size reduction.

    Sample size reduction occurs when imposing a HSR filing test
    or equilibrium condition under MNL demand.
    """

    HSR_NTH = 1.666667
    """
    HSR filing test with merger-firm shares at (1:1, 10:1) to n-th firm share.

    When the n-firm's revenues in a market of n firms are assumed to match
    the lower threshold for the size-of-person test. In effect, this version
    for the test assumes that at least one firm in every investigated market
    has revenues exactly equal to the dollar amount of the lower threshold for
    the HSR size-of-person test.
    """

    HSR_TEN = 1.234567
    """
    HSR filing test with merger-firm relative shares of 10:1.

    When smaller merging-firm's revenues are assumed to match
    the lower threshold for the size-of-person test.

    This figure is updated to `round(1e5 / 32500, 2)` in the constructor
    for the class, :class:`.data_generation.MarketSample`, when shares are
    drawn from the uniform distribution.
    """

    HSR_TEN_UNI = round(1e3 / 325, 2)
    """
    HSR filing test with merger-firm relative shares of 10:1.

    When smaller merging-firm's revenues are assumed to match
    the lower threshold for the size-of-person test.

    This figure is updated to `round(1e5 / 32500, 2)` in the constructor
    for the class, :class:`.data_generation.MarketSample`, when shares are
    drawn from the uniform distribution with lower bound 0.01 and upper bound
    1.0 to preserve the sample size.
    """

    HSR_RNDB = 1.5
    """
    HSR filing test for testing implicit lower enforcement bound merging-firm share.

    The test share vector is drawn from the Beta distribution with two parameters given by
    :attr:`HSR_BETA_PARMS`.
    """

    HSR_RNDU = 20.0
    """
    HSR filing test for randomly sampled test share threshold.

    For testing the intrinsic impact of HSR filing tests on enforcement rates.
    """

    MNL_DEP = 1.25
    """
    For restricted PCM's.

    When merging firm's PCMs are constrained for consistency with f.o.c.s from
    profit maximization under Nash-Bertrand oligopoly with MNL demand.

    Updated in the :attr:`.data_generation.MarketSample.generate_data()` method
    when PCMs are drawn from the uniform distribution.
    """

    MNL_DEP_UNI = round(1e3 / 340, 3)
    """
    For restricted PCM's, when shares are drawn from the uniform distribution.

    Updated when PCMs are restricted as in :attr:`MNL_DEP` and shares are drawn from
    the uniform distribution.
    """

    ONE = 1.00
    """When initial set of draws is not restricted in any way."""


@frozen
class MarketsData:
    """Container for generated market sample dataset."""

    mktshr_array: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """Generated market shares, with zeros for markets with fewer firms than the maximum."""

    pcm_array: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """Generated prices; normalized to 1 in default specification)"""

    price_array: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """Generated price-cost margins (PCM)"""

    divratio_array: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """Diversion ratios between the merging firms"""

    hhi_delta: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """Change in HHI from combination of merging firms"""

    aggregate_purchase_prob: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal),
        default=EMPTY_ARRAYDOUBLE,
        converter=ArrayDouble,
    )
    """
    One (1) minus probability that the outside good is chosen

    Converts market shares to choice probabilities by multiplication.
    """

    fcounts: ArrayUINT8 = field(
        eq=cmp_using(eq=np.array_equal), default=EMPTY_ARRAYUINT8, converter=ArrayUINT8
    )
    """Number of firms in market"""

    nth_firm_share: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal),
        default=EMPTY_ARRAYDOUBLE,
        converter=ArrayDouble,
    )
    """Market-share of n-th firm

    Relevant for testing draws that do or
    do not meet HSR filing thresholds.
    """

    hhi_post: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal),
        default=EMPTY_ARRAYDOUBLE,
        converter=ArrayDouble,
    )
    """Post-merger contribution to Herfindahl-Hirschman Index (HHI)"""

    def to_h5bin(self) -> bytes:
        """Save market sample data to HDF5 file."""
        byte_stream = io.BytesIO()
        with h5py.File(byte_stream, "w") as _h5f:
            for _a in self.__attrs_attrs__:
                if all((
                    (_arr := getattr(self, _a.name)).any(),
                    # not np.isnan(next(_arr.flat)),
                )):
                    _h5f.create_dataset(
                        _a.name,
                        data=_arr,
                        fletcher32=True,
                        **hdf5plugin.Zstd(),  # type: ignore[attr-defined]
                    )
        return byte_stream.getvalue()

    @classmethod
    def from_h5f(
        cls, _hfh: io.BufferedReader | zipfile.ZipExtFile | IO[bytes]
    ) -> MarketsData:
        """Load market sample data from HDF5 file."""
        with h5py.File(_hfh, "r") as _h5f:
            _retval = cls(**{_a: _h5f[_a][:] for _a in _h5f})
        return _retval


@frozen
class MarketSharesData:
    """Container for generated market shares.

    Includes related measures of market structure
    and aggregate purchase probability.
    """

    mktshr_array: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """All-firm shares (with two merging firms)"""

    fcounts: ArrayUINT8 | ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), default=EMPTY_ARRAYUINT8, converter=ArrayUINT8
    )
    """All-firm-count for each draw"""

    nth_firm_share: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal),
        default=EMPTY_ARRAYDOUBLE,
        converter=ArrayDouble,
    )
    """Market-share of n-th firm"""

    aggregate_purchase_prob: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal),
        default=EMPTY_ARRAYDOUBLE,
        converter=ArrayDouble,
    )
    """Converts market shares to choice probabilities by multiplication."""


@frozen
class PricesData:
    """Container for generated price array, and related."""

    price_array: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """Merging-firms' prices"""

    hsr_filing_test: ArrayBoolean = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayBoolean
    )
    """Flags draws as meeting HSR filing thresholds or not"""


@frozen
class MarginsData:
    """Container for generated margin array and related MNL test array."""

    pcm_array: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """Merging-firms' PCMs"""

    mnl_test: ArrayBoolean = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayBoolean
    )
    """Flags infeasible observations as False and rest as True

    Applying restrictions from Bertrand-Nash oligopoly with MNL demand results
    in some draws of Firm 2 PCM falling outside the feasible interval, :math:`[0, 1]`
    for certain combinations of merging firms shares as initially drawn. Such draws
    are flagged as infeasible (False) in :code:`mnl_test` while draws with
    feasible PCM values flagged True. This array is used to exclude infeasible draws
    when imposing MNL demand in simulations.
    """


@this_yaml.register_class
@enum.unique
class INVResolution(str, Enameled):
    """Report investigations resulting in clearance; enforcement; or both, respectively."""

    CLRN = "clearance"
    ENFT = "enforcement"
    BOTH = "clearance and enforcement, respectively"


@frozen
class UPPTestRegime:
    """Configuration for UPP tests."""

    resolution: INVResolution = field(kw_only=False, default=INVResolution.ENFT)
    """Whether to test clearance, enforcement."""

    @resolution.validator
    def _resvdtr(
        _i: UPPTestRegime, _a: Attribute[INVResolution], _v: INVResolution
    ) -> None:
        if _v == INVResolution.BOTH:
            raise ValueError(
                "GUPPI test cannot be performed with both resolutions; only useful for reporting"
            )
        elif _v not in {INVResolution.CLRN, INVResolution.ENFT}:
            raise ValueError(
                f"Must be one of, {INVResolution.CLRN!r} or {INVResolution.ENFT!r}"
            )

    guppi_aggregator: UPPAggrSelector = field(kw_only=False)
    """Aggregator for GUPPI test."""

    @guppi_aggregator.default
    def _gad(_i: UPPTestRegime) -> UPPAggrSelector:
        return (
            UPPAggrSelector.MIN
            if _i.resolution == INVResolution.ENFT
            else UPPAggrSelector.MAX
        )

    divr_aggregator: UPPAggrSelector = field(kw_only=False)
    """Aggregator for diversion ratio test."""

    @divr_aggregator.default
    def _dad(_i: UPPTestRegime) -> UPPAggrSelector:
        return _i.guppi_aggregator


@frozen
class UPPTestsCounts:
    """Counts of markets resolved as specified.

    Resolution may be either :attr:`INVResolution.ENFT`,
    :attr:`INVResolution.CLRN`, or :attr:`INVResolution.BOTH`.
    In the case of :attr:`INVResolution.BOTH`, two columns of counts
    are returned: one for each resolution.
    """

    ByFirmCount: ArrayBIGINT = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayBIGINT
    )
    ByDelta: ArrayBIGINT = field(eq=cmp_using(eq=np.array_equal), converter=ArrayBIGINT)
    ByHHIandDelta: ArrayBIGINT = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayBIGINT
    )


for _typ in (SeedSequenceData, MarketShareSpec, PCMSpec, UPPTestsCounts, UPPTestRegime):
    yamlize_attrs(_typ)
