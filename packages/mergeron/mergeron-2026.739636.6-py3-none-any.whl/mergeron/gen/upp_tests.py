"""Methods to compute intrinsic enforcement/clearance rates from generated market data."""

from collections.abc import Sequence
from typing import TypedDict

import numpy as np
from numpy.random import SeedSequence

from .. import (  # noqa
    EMPTY_ARRAYBIGINT,
    VERSION,
    ArrayBIGINT,
    ArrayBoolean,
    ArrayDouble,
    ArrayFloat,
    ArrayINT,
    UPPAggrSelector,
)
from ..core import MGThresholds
from . import INVResolution, MarketsData, UPPTestRegime, UPPTestsCounts
from . import enforcement_stats as esl

__version__ = VERSION


class INVRESCntsArgs(TypedDict, total=False):
    """Keyword arguments of function, :code:`sim_enf_cnts`."""

    sample_size: int
    seed_seq_list: Sequence[SeedSequence] | None
    nthreads: int


def compute_upp_test_counts(
    _market_data_sample: MarketsData,
    _upp_test_parms: MGThresholds,
    _upp_test_regime: UPPTestRegime,
    /,
) -> UPPTestsCounts:
    """Estimate enforcement and clearance counts from market data sample.

    Parameters
    ----------
    _market_data_sample
        Market data sample

    _upp_test_parms
        Threshold values for various Guidelines criteria

    _upp_test_regime
        Specifies whether to analyze enforcement, clearance, or both
        and the GUPPI and diversion ratio aggregators employed, with
        default being to analyze enforcement based on the maximum
        merging-firm GUPPI and maximum diversion ratio between the
        merging firms

    Returns
    -------
    UPPTestsCounts
        Enforced and cleared counts

    """
    g_bar_, divr_bar_, cmcr_bar_, ipr_bar_ = (
        getattr(_upp_test_parms, _f) for _f in ("guppi", "dr", "cmcr", "ipr")
    )

    _divratio_array, _frmshr_array, _pcm_array, _price_array = (
        getattr(_market_data_sample, _f)[:, :2]
        for _f in ("divratio_array", "mktshr_array", "pcm_array", "price_array")
    )

    guppi_array, ipr_array, cmcr_array = (
        np.empty_like(_divratio_array).view(ArrayDouble) for _ in range(3)
    )

    np.einsum(
        "ij,ij,ij->ij",
        _divratio_array,
        _pcm_array[:, ::-1],
        _price_array[:, ::-1] / _price_array,
        out=guppi_array,
    )

    np.divide(
        np.einsum("ij,ij->ij", _pcm_array, _divratio_array),
        1 - _divratio_array,
        out=ipr_array,
    )

    np.divide(ipr_array, 1 - _pcm_array, out=cmcr_array)

    (divr_test_vector,) = _compute_test_vector_seq(
        (_divratio_array,), _frmshr_array, _upp_test_regime.divr_aggregator
    )

    (guppi_test_vector, cmcr_test_vector, ipr_test_vector) = _compute_test_vector_seq(
        (guppi_array, cmcr_array, ipr_array),
        _frmshr_array,
        _upp_test_regime.guppi_aggregator,
    )
    del cmcr_array, ipr_array, guppi_array

    if _upp_test_regime.resolution == INVResolution.ENFT:
        upp_test_arrays = np.hstack((
            guppi_test_vector >= g_bar_,
            (guppi_test_vector >= g_bar_) | (divr_test_vector >= divr_bar_),
            cmcr_test_vector >= cmcr_bar_,
            ipr_test_vector >= ipr_bar_,
        ))
    else:
        upp_test_arrays = np.hstack((
            guppi_test_vector < g_bar_,
            (guppi_test_vector < g_bar_) & (divr_test_vector < divr_bar_),
            cmcr_test_vector < cmcr_bar_,
            ipr_test_vector < ipr_bar_,
        ))

    fcounts, hhi_delta, hhi_post = (
        getattr(_market_data_sample, _g) for _g in ("fcounts", "hhi_delta", "hhi_post")
    )

    # Clearance counts by firm count
    enf_cnts_sim_byfirmcount_array = (
        EMPTY_ARRAYBIGINT
        if not len(fcounts)
        else esl.enf_cnts_byfirmcount(
            np.hstack((fcounts, np.ones_like(fcounts), upp_test_arrays)).view(
                ArrayBIGINT
            )
        )
    )

    # Clearance counts by post-merger HHI and ΔHHI
    if len(hhi_post) == 0 or np.isnan(next(hhi_post.flat)):
        hhi_post_ranged = EMPTY_ARRAYBIGINT
        hhi_delta_ranged = esl.hhi_delta_ranger(hhi_delta).astype(int)

        enf_cnts_sim_bydelta_array = esl.enf_cnts_bydelta(
            np.hstack(
                (hhi_delta_ranged, np.ones_like(hhi_delta_ranged), upp_test_arrays),
                dtype=int,
            ).view(ArrayBIGINT)
        )
        enf_cnts_sim_byhhianddelta_array = EMPTY_ARRAYBIGINT
    else:
        hhi_post_ranged = esl.hhi_post_ranger(hhi_post).astype(int)
        hhi_delta_ranged = esl.hhi_delta_ranger(hhi_delta).astype(int)

        enf_cnts_sim_byhhianddelta_array_raw = np.hstack(
            (
                hhi_post_ranged,
                hhi_delta_ranged,
                np.ones_like(hhi_delta_ranged),
                upp_test_arrays,
            ),
            dtype=int,
        ).view(ArrayBIGINT)

        enf_cnts_sim_bydelta_array = esl.enf_cnts_bydelta(
            enf_cnts_sim_byhhianddelta_array_raw[:, 1:]  # type: ignore
        )
        enf_cnts_sim_byhhianddelta_array = esl.enf_cnts_byhhianddelta(
            enf_cnts_sim_byhhianddelta_array_raw
        )

    return UPPTestsCounts(
        ByFirmCount=enf_cnts_sim_byfirmcount_array,
        ByDelta=enf_cnts_sim_bydelta_array,
        ByHHIandDelta=enf_cnts_sim_byhhianddelta_array,
    )


def _compute_test_vector_seq(
    _test_data_seq: tuple[ArrayDouble, ...],
    _weights: ArrayDouble,
    _aggregator: UPPAggrSelector,
) -> tuple[ArrayDouble, ...]:
    if _aggregator in {UPPAggrSelector.CPA, UPPAggrSelector.CPD, UPPAggrSelector.CPG}:
        _wgts = _weights[:, ::-1] / np.einsum("ij->i", _weights)[:, None]
    elif _aggregator in {UPPAggrSelector.OSA, UPPAggrSelector.OSD, UPPAggrSelector.OSG}:
        _wgts = _weights / np.einsum("ij->i", _weights)[:, None]
    elif _aggregator in {UPPAggrSelector.AVG, UPPAggrSelector.DIS, UPPAggrSelector.GMN}:
        _wgts = (_w := np.ones((1, 2))) / _w.sum()
    else:
        # Weights not used for min, max
        _wgts = np.array([], float)

    # Use weights calculated above to compute average, distance, and geometric mean:
    if _aggregator in {UPPAggrSelector.AVG, UPPAggrSelector.CPA, UPPAggrSelector.OSA}:
        test_vector_seq = (
            np.einsum("ij,ij->i", _wgts, _g)[:, None] for _g in _test_data_seq
        )
    elif _aggregator in {UPPAggrSelector.DIS, UPPAggrSelector.CPD, UPPAggrSelector.OSD}:
        test_vector_seq = (
            np.sqrt(np.einsum("ij,ij,ij->i", _wgts, _g, _g))[:, None]
            for _g in _test_data_seq
        )
    elif _aggregator in {UPPAggrSelector.CPG, UPPAggrSelector.GMN, UPPAggrSelector.OSG}:
        test_vector_seq = (
            np.expm1(np.einsum("ij,ij->i", _wgts, np.log1p(_g)))[:, None]
            for _g in _test_data_seq
        )
    elif _aggregator == UPPAggrSelector.MAX:
        test_vector_seq = (_g.max(axis=1, keepdims=True) for _g in _test_data_seq)
    elif _aggregator == UPPAggrSelector.MIN:
        test_vector_seq = (_g.min(axis=1, keepdims=True) for _g in _test_data_seq)
    else:
        raise ValueError("GUPPI/diversion ratio aggregation method is invalid.")
    return tuple(_t.view(ArrayDouble) for _t in test_vector_seq)


if __name__ == "__main__":
    print(
        "This module defines functions for generating UPP test arrays "
        "and UPP test enforcement-counts on market samples."
    )
