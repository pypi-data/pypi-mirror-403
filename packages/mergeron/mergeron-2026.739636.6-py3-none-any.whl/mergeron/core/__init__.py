"""Constants, types, objects and functions used within this sub-package."""

from __future__ import annotations

import shutil
from importlib.resources import as_file
from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np
from attrs import cmp_using, field, frozen

from .. import VERSION, WORK_DIR, ArrayBIGINT, ArrayDouble, ArrayFloat, yamlize_attrs
from .. import data as mdat
from .. import this_yaml as this_yaml
from .. import yaml_rt_mapper as yaml_rt_mapper

if TYPE_CHECKING:
    from ruamel import yaml

__version__ = VERSION

PKG_WORK_DIR = WORK_DIR

DEFAULT_DIST_PARMS = ArrayFloat([0.0, 1.0])
DEFAULT_BETA_DIST_PARMS = ArrayFloat([1.0, 1.0])


# https://stackoverflow.com/questions/54611992/
# https://numpy.org/doc/stable/user/basics.subclassing.html#basics-subclassing
@this_yaml.register_class
class PubYear(int):
    """
    Type definition for Guidelines publication year.

    We restrict to publication years Guidelines in which the Agencies indicate
    the use of concentration screens for unilateral competitive effects from
    horizontal mergers.
    """

    def __new__(cls, _y: int) -> PubYear:
        """Raise ValueError if argument not match a Guidelines publication year."""
        if _y not in {1992, 2010, 2023}:
            raise ValueError(
                f"Value given, {_y} is not a valid Guidelines publication year here."
            )
        return super().__new__(cls, _y)

    @classmethod
    def to_yaml(
        cls, _r: yaml.representer.RoundTripRepresenter, _d: PubYear
    ) -> yaml.ScalarNode:
        """Serialize PubYear."""
        return _r.represent_scalar(f"!{cls.__name__}", f"{_d}")

    @classmethod
    def from_yaml(
        cls, _c: yaml.constructor.RoundTripConstructor, _n: yaml.ScalarNode
    ) -> PubYear:
        """Deserialize PubYear."""
        return cls(int(_n.value))


@frozen
class MGThresholds:
    """Thresholds for Guidelines standards."""

    delta: float
    fc: float
    rec: float
    guppi: float
    dr: float
    cmcr: float
    ipr: float


@frozen
class GuidelinesBoundary:
    """Represents Guidelines boundary analytically."""

    coordinates: ArrayDouble = field(converter=ArrayDouble)
    """Market-share pairs as Cartesian coordinates of points on the boundary."""

    area: float
    """Area under the boundary."""


WORK_DIR = globals().get("WORK_DIR", PKG_WORK_DIR)
"""Redefined, in case the user defines WORK_DIR between module imports."""

FID_WORK_DIR = WORK_DIR / "FTCData"
if not FID_WORK_DIR.is_dir():
    FID_WORK_DIR.mkdir(parents=True)

INVDATA_ARCHIVE_PATH = WORK_DIR / mdat.FTC_MERGER_INVESTIGATIONS_DATA.name
if not INVDATA_ARCHIVE_PATH.is_file():
    with as_file(mdat.FTC_MERGER_INVESTIGATIONS_DATA) as _fid:
        shutil.copy2(_fid, INVDATA_ARCHIVE_PATH)

MGNDATA_ARCHIVE_PATH = WORK_DIR / "damodaran_margin_data_serialized.zip"
if not MGNDATA_ARCHIVE_PATH.is_file():
    with as_file(mdat.DAMODARAN_MARGIN_DATA) as _f:
        shutil.copy2(_f, MGNDATA_ARCHIVE_PATH)


TABLE_TYPES = ("ByHHIandDelta", "ByFirmCount")
CONC_TABLE_ALL = "Table 3.1"
CNT_TABLE_ALL = "Table 4.1"

TTL_KEY = 86825
CONC_HHI_DICT = {
    "0 - 1,799": 0,
    "1,800 - 1,999": 1800,
    "2,000 - 2,399": 2000,
    "2,400 - 2,999": 2400,
    "3,000 - 3,999": 3000,
    "4,000 - 4,999": 4000,
    "5,000 - 6,999": 5000,
    "7,000 - 10,000": 7000,
    "TOTAL": TTL_KEY,
}
CONC_DELTA_DICT = {
    "0 - 100": 0,
    "100 - 200": 100,
    "200 - 300": 200,
    "300 - 500": 300,
    "500 - 800": 500,
    "800 - 1,200": 800,
    "1,200 - 2,500": 1200,
    "2,500 - 5,000": 2500,
    "TOTAL": TTL_KEY,
}
CNT_FCOUNT_DICT = {
    "2 to 1": 2,
    "3 to 2": 3,
    "4 to 3": 4,
    "5 to 4": 5,
    "6 to 5": 6,
    "7 to 6": 7,
    "8 to 7": 8,
    "9 to 8": 9,
    "10 to 9": 10,
    "10 +": 11,
    "TOTAL": TTL_KEY,
}


type INVData = MappingProxyType[
    str, MappingProxyType[str, MappingProxyType[str, INVTableData]]
]
type INVData_in = dict[str, dict[str, dict[str, INVTableData]]]


@frozen
class INVTableData:
    """Represents individual table of FTC merger investigations data."""

    industry_group: str
    additional_evidence: str
    data_array: ArrayBIGINT = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayBIGINT
    )


@frozen
class EmpiricalMarginData:
    """Container for gross margin data from Prof. Damodaran, NYU.

    Along with the industry average gross margins and firm counts, we report
    overall statistics, and a bandwidth estimate for kernel density
    estimation.
    """

    average_gross_margins: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """
    Weighted average gross margins by industry, averaged across the available years,
    with firm counts as weights. Only positive average margins are included in
    estimation.
    """

    firm_counts: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """Number of firms by industry, averaged across the available years with positive
    average industry margins."""

    margin_stats: ArrayDouble = field(
        eq=cmp_using(eq=np.array_equal), converter=ArrayDouble
    )
    """Weighted average, weighted standard error, minimum, and maximum across industries."""

    bandwidth: float
    """
    Kernel bandwidth estimated using the Improved Sheather-Jones method discussed in
    [#r1]_ and implemented in [#r2]_. Used for adding Gaussian noise when resampling
    with replacement from industry average margins.

    .. [#r1] Z. I. Botev. J. F. Grotowski. D. P. Kroese. "Kernel density estimation via
      diffusion." Ann. Statist. 38 (5) 2916 - 2957, October 2010.
      https://doi.org/10.1214/10-AOS799.

    .. [#r2] KDEpy, https://kdepy.readthedocs.io.
    """


for _typ in (INVTableData, EmpiricalMarginData, MGThresholds, GuidelinesBoundary):
    yamlize_attrs(_typ)
