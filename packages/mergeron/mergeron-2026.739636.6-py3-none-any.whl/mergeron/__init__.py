"""Variables, types, objects and functions used throughout the package."""

from __future__ import annotations

import enum
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

import mpmath  # type: ignore
import numpy as np

from . import _serialization

this_yaml = _serialization.this_yaml
yaml_rt_mapper = _serialization.yaml_rt_mapper
yamlize_attrs = _serialization.yamlize_attrs

if sys.version_info >= (3, 14):
    import zipfile as zipfile_conditional
else:
    from backports.zstd import zipfile as zipfile_conditional

if TYPE_CHECKING:
    from numpy.typing import DTypeLike, NDArray
    from ruamel import yaml

# Need the two-step re-export for sphinx/autoapi
zipfile = zipfile_conditional

VERSION = "2026.739636.6"

__version__ = VERSION

PKG_NAME: str = Path(__file__).parent.name

WORK_DIR: Path = globals().get("WORK_DIR", Path.home() / PKG_NAME)
"""
If defined, the global variable WORK_DIR is used as a data store.

If the user does not define WORK_DIR, a subdirectory in
the user's home directory, named for this package, is
created/reused.
"""
if not WORK_DIR.is_dir():
    WORK_DIR.mkdir(parents=False)

DEFAULT_REC = globals().get("DEFAULT_REC", 0.85)
"""Default recapture rate.

Can be overridden at the user's specification.
Overriding the default recapture rate requires that
this object is redefined **before** instantiating any classes
or calling any functions that invoke this object.
"""

NTHREADS = 32

type MPFloat = mpmath.mpf
type MPMatrix = mpmath.matrix

np.set_printoptions(precision=28, floatmode="fixed", legacy=False)


# Yamelized Enum
class Enameled(enum.Enum):
    """Add YAML representer, constructor for enum.Enum."""

    @classmethod
    def to_yaml(
        cls, _r: yaml.representer.RoundTripRepresenter, _d: enum.Enum
    ) -> yaml.ScalarNode:
        """Serialize enumerations by .name, not .value."""
        return _r.represent_scalar(
            f"!{super().__getattribute__(cls, '__name__')}", f"{_d.name}"
        )

    @classmethod
    def from_yaml(
        cls, _c: yaml.constructor.RoundTripConstructor, _n: yaml.ScalarNode
    ) -> enum.EnumType:
        """Deserialize enumeration serialized by .name."""
        retval: enum.EnumType = super().__getattribute__(cls, _n.value)
        return retval


@this_yaml.register_class
@enum.unique
class RECForm(str, Enameled):
    R"""For derivation of recapture rate from market shares.

    With :math:`\mathscr{N}` a set of firms, each supplying a
    single differentiated product, and :math:`\mathscr{M} \subset \mathscr{N}`
    a putative relevant product market, with
    :math:`d_{ij}` denoting diversion ratio from good :math:`i` to good :math:`j`,
    :math:`s_i` denoting market shares, and
    :math:`\overline{r}` the default market recapture rate,
    market recapture rates for the respective products may be specified
    as having one of the following forms:
    """

    FIXED = "fixed"
    R"""Given, :math:`\overline{r}`,

    .. math::

        REC_i = \overline{r} {\ } \forall {\ } i \in \mathscr{M}

    """

    INOUT = "inside-out"
    R"""
    Given, :math:`\overline{r}, s_i {\ } \forall {\ } i \in \mathscr{M}`, with
    :math:`s_{min} = \min(s_1, s_2)`,

    .. math::

        REC_i = \frac{\overline{r} (1 - s_i)}{1 - (1 - \overline{r}) s_{min} - \overline{r} s_i}
        {\ } \forall {\ } i \in \mathscr{M}

    The default within this package.
    """

    OUTIN = "outside-in"
    R"""
    Given, :math:`d_{ij} {\ } \forall {\ } i, j \in \mathscr{M}, i \neq j`,

    .. math::

        REC_i = {\sum_{j \in \mathscr{M}}^{j \neq i} d_{ij}}
        {\ } \forall {\ } i \in \mathscr{M}

    """


@this_yaml.register_class
@enum.unique
class UPPAggrSelector(str, Enameled):
    """Aggregator for GUPPI and diversion ratio estimates."""

    AVG = "average"
    CPA = "cross-product-share weighted average"
    CPD = "cross-product-share weighted distance"
    CPG = "cross-product-share weighted geometric mean"
    DIS = "symmetrically-weighted distance"
    GMN = "geometric mean"
    MAX = "max"
    MIN = "min"
    OSA = "own-share weighted average"
    OSD = "own-share weighted distance"
    OSG = "own-share weighted geometric mean"


# redefine numpy testing functions to modify default tolerances
def allclose(
    _a: ArrayFloat | ArrayINT | float | int,
    _b: ArrayFloat | ArrayINT | float | int,
    /,
    *,
    rtol: float = 1e-14,
    atol: float = 1e-15,
    equal_nan: bool = True,
) -> bool:
    """Redefine native numpy function with updated default tolerances."""
    return np.allclose(_a, _b, atol=atol, rtol=rtol, equal_nan=equal_nan)


def assert_allclose(  # noqa: PLR0913
    _a: ArrayFloat | ArrayINT | float | int,
    _b: ArrayFloat | ArrayINT | float | int,
    /,
    *,
    rtol: float = 1e-14,
    atol: float = 1e-15,
    equal_nan: bool = True,
    err_msg: str = "",
    verbose: bool = False,
    strict: bool = True,
) -> None:
    """Redefine native numpy function with updated default tolerances, type-enforcing."""
    return np.testing.assert_allclose(
        _a,
        _b,
        atol=atol,
        rtol=rtol,
        equal_nan=equal_nan,
        err_msg=err_msg,
        verbose=verbose,
        strict=True,
    )


# https://numpy.org/devdocs/user/basics.subclassing.html#slightly-more-realistic-example-attribute-added-to-existing-array
@this_yaml.register_class
class TypedNDArray(np.ndarray):
    """NDArray with type specification."""

    def __new__(  # noqa: D102
        cls,
        _arr: Sequence[
            bool | float | int | MPFloat | Sequence[bool | float | int | MPFloat]
        ]
        | np.ndarray,
        _type: DTypeLike,  # np.bool_ | np.float64 | np.floating | np.int64 | np.integer | np.uint8,
        /,
        *,
        info: dict[str, Any] | None = None,
    ) -> TypedNDArray:
        if not hasattr(_arr, "__len__") or isinstance(_arr, str):
            raise ValueError(f"Invalid first argument, {_arr!r}")

        _type = _type or type(np.ravel(_arr)[0])

        _dtype_dict: dict[DTypeLike, DTypeLike] = {
            np.bool_: bool,
            np.floating: float,
            np.integer: int,
        }
        _dtype = object if _type == MPFloat else _dtype_dict.get(_type, _type)

        if not len(np.ravel(_arr)):
            _arr = np.array([], dtype=_dtype)
        elif isinstance(np.ravel(_arr)[0], Sequence | np.ndarray) and isinstance(
            np.ravel(_arr)[0], mpmath.mpf
        ):
            if not np.issubdtype(_type, np.floating):
                raise ValueError(
                    "Array of MPFloat objects can only be converted to "
                    f"ArrayFloat, ArrayDouble, or ArrayMPFloat, not {_type!r}."
                )
            _arr = np.asarray(_arr, float)
        elif not np.issubdtype((_dt := np.asarray(_arr, _dtype).dtype), _type):
            raise ValueError(
                f"Array type, {_dt!r}, is not compatible with target dtype, {_type}."
            )
        obj = np.asarray(_arr, _dtype).view(cls)
        obj.info = info
        return obj

    def __array_finalize__(self, obj: np.ndarray | None) -> None:  # noqa: D105
        if obj is None:
            return
        self.info = getattr(obj, "info", None)
        return

    @classmethod
    def to_yaml(
        cls, _r: yaml.representer.RoundTripRepresenter, _d: np.ndarray
    ) -> yaml.SequenceNode:
        """Serialize TypedNDArray."""
        return _r.represent_sequence(
            f"!{super().__getattribute__(cls, '__name__')}", (_d.tolist(), _d.dtype.str)
        )

    @classmethod
    def from_yaml(
        cls, _c: yaml.constructor.RoundTripConstructor, _n: yaml.SequenceNode
    ) -> TypedNDArray:
        """Deserialize TypedNDArray."""
        _data = np.asarray(*_c.construct_sequence(_n, deep=True))
        return TypedNDArray.__new__(cls, _data, _data.dtype).view(cls)


@this_yaml.register_class
class ArrayBoolean(TypedNDArray):
    """Array of booleans."""

    def __new__(cls, _arr: Sequence[bool] | NDArray[np.bool_]) -> ArrayBoolean:  # noqa: D102
        return super().__new__(cls, _arr, np.bool_).view(cls)


@this_yaml.register_class
class ArrayDouble(TypedNDArray):
    """Array of double-precision floats."""

    def __new__(  # noqa: D102
        cls, _arr: Sequence[float | Sequence[float]] | NDArray[np.float64]
    ) -> ArrayDouble:
        return super().__new__(cls, _arr, np.float64).view(cls).view(cls)


@this_yaml.register_class
class ArrayFloat(TypedNDArray):
    """Array of floats, any precision supported by numpy."""

    def __new__(  # noqa: D102
        cls, _arr: Sequence[float | Sequence[float]] | NDArray[np.floating]
    ) -> ArrayFloat:
        return super().__new__(cls, _arr, np.floating).view(cls).view(cls)


@this_yaml.register_class
class ArrayBIGINT(TypedNDArray):
    """Array of 64-bit integers."""

    def __new__(cls, _arr: Sequence[int] | NDArray[np.int64]) -> ArrayBIGINT:  # noqa: D102
        return super().__new__(cls, _arr, np.int64).view(cls)


@this_yaml.register_class
class ArrayINT(TypedNDArray):
    """Array of integers, any precision supported by numpy."""

    def __new__(cls, _arr: Sequence[int] | NDArray[np.integer]) -> ArrayINT:  # noqa: D102
        return super().__new__(cls, _arr, np.integer).view(cls)


@this_yaml.register_class
class ArrayMPFloat(TypedNDArray):
    """Array of arbitrary-precision floats, mpmath.mpf()s."""

    def __new__(cls, _arr: Sequence[MPFloat] | np.ndarray) -> ArrayMPFloat:  # noqa: D102  # type: ignore
        if not hasattr(next(np.asarray(_arr).flat), "mpf_convert_arg"):
            raise ValueError("Data array cannot be converted to ArrayMPFloat.")
        return super().__new__(cls, _arr, np.object_).view(cls)


@this_yaml.register_class
class ArrayUINT8(TypedNDArray):
    """Array of 8-bit unsigned integers."""

    def __new__(cls, _arr: NDArray[np.uint8]) -> ArrayUINT8:  # noqa: D102
        return super().__new__(cls, _arr, np.uint8).view(cls)


EMPTY_ARRAYBIGINT = ArrayBIGINT(np.array([], int))
EMPTY_ARRAYBOOLEAN = ArrayBIGINT(np.array([], bool))
EMPTY_ARRAYDOUBLE = ArrayDouble(np.array([], float))
EMPTY_ARRAYUINT8 = ArrayUINT8(np.array([], np.uint8))
