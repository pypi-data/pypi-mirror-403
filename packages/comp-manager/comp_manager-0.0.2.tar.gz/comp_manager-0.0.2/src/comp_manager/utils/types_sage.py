# pragma: exclude file - this file is not covered in case sage is not available
from typing import Any, TypedDict, Literal, NotRequired

try:
    from sage.rings.complex_mpfr import ComplexField_class, ComplexNumber
    from sage.rings.integer_ring import IntegerRing_class
    from sage.rings.number_field.number_field import NumberField_generic
    from sage.rings.number_field.number_field_element import NumberFieldElement
    from sage.rings.rational import Rational
    from sage.rings.integer import Integer
    from sage.rings.rational_field import RationalField
    from sage.rings.real_mpfr import RealNumber, RealField_class

    Integer_t = Integer | int
    Real_t = RealNumber | float
    Complex_t = ComplexNumber | complex
    RingElement_t = Integer_t | Real_t | Complex_t | NumberFieldElement
    Ring_t = (
        RealField_class
        | ComplexField_class
        | RationalField
        | NumberField_generic
        | IntegerRing_class
    )

    def get_prec(x: Any) -> int:
        """
        Get the precision of a Sage object.
        """
        if isinstance(x, (RealNumber, ComplexNumber)):
            return int(x.prec())
        if isinstance(x, (Integer_t, Rational)):
            return 0
        return 53
except ImportError:  # pragma: no cover
    Integer_t = int
    Real_t = float
    Complex_t = complex
    Ring_t = None
    RingElement_t = int | float | complex

    def get_prec(x: Any) -> int:
        """
        Get the precision of a standard type.
        """
        if isinstance(x, int):
            return 0
        return 53


class TypedDictType(TypedDict):
    r"""
    Typed dictionary type.
    """

    __type__: Literal[
        "ring", "element", "matrix", "number_field", "tuple", "vector", "number_field_ideal"
    ]
    name: NotRequired[str]


class NumberFieldJson(TypedDict):
    r"""
    JSON representation of a number field.
    """

    __type__: Literal["number_field"]
    polynomial: str
    name: NotRequired[str]
    names: list[str]
    embedding: NotRequired[str]


class NumberFieldIdealJson(TypedDict):
    r"""
    JSON representation of a number field ideal.
    """

    __type__: Literal["number_field_ideal"]
    number_field: NumberFieldJson
    gens: list[Any]


class TupleJSON(TypedDict):
    r"""
    JSON representation of a tuple.
    """

    __type__: Literal["tuple"]
    entries: list[Any]


class RingJson(TypedDictType):
    r"""
    JSON representation of a ring.
    """

    prec: NotRequired[int]
    field: NotRequired[NumberFieldJson]


class RingElementJson(TypedDictType):
    r"""
    JSON representation of a ring element.
    """

    parent: RingJson
    value: str


class VectorJson(TypedDictType):
    r"""
    JSON representation of a vector.
    """

    base_ring: RingJson
    entries: list[str]


class MatrixJson(TypedDictType):
    r"""
    JSON representation of a matrix.
    """

    base_ring: RingJson
    entries: list[list[str]]


def is_typed_dict(obj: object, model: object) -> bool:
    r"""
    Check if an object is a typed dictionary.

    INPUT:

    - ``obj`` -- object to check
    - ``model`` -- model to check against

    OUTPUT: True if the object is a typed dictionary, else False
    """
    if not isinstance(obj, dict):
        return False
    required_keys = getattr(model, "__required_keys__", None)
    if not required_keys:
        return False
    type = obj.get("__type__", None)
    valid_types = TypedDictType.__annotations__["__type__"].__args__
    return type in valid_types and all(key in obj for key in required_keys)
