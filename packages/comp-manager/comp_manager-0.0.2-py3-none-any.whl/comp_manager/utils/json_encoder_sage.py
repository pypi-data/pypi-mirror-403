# pragma: exclude file - this file is not covered in case sage is not available
import json
from json import JSONDecodeError
from typing import Any, cast
import warnings
from .types_sage import (
    RingElementJson,
    RingJson,
    NumberFieldJson,
    NumberFieldIdealJson,
    MatrixJson,
    TypedDictType,
    TupleJSON,
    VectorJson,
    Ring_t,
    RingElement_t,
    Integer_t,
    Real_t,
    get_prec,
    Complex_t,
    is_typed_dict,
)
from .json_encoder import JSONEncoder, JSONDecoder

warnings.simplefilter("ignore")

try:
    from sage.structure.element import Matrix, Vector
    from sage.rings.number_field.number_field import NumberField_generic
    from sage.modules.free_module_element import vector
    from sage.all import ZZ
    from sage.matrix.constructor import matrix
    from sage.rings.complex_mpfr import ComplexField, ComplexField_class
    from sage.rings.number_field.number_field import NumberField
    from sage.rings.number_field.number_field_element import NumberFieldElement
    from sage.rings.number_field.number_field_ideal import NumberFieldFractionalIdeal
    from sage.rings.rational import Rational
    from sage.rings.rational_field import RationalField
    from sage.rings.integer_ring import IntegerRing_class, IntegerRing
    from sage.rings.real_mpfr import RealField, RealField_class  #

    class SageJSONEncoder(JSONEncoder):
        r"""
        JSON encoder for sage objects.
        """

        def encode(self, o: object) -> str:
            r"""
            Convert a sage object to a JSON string.
            """
            new_o: object
            if isinstance(o, dict):
                new_o = {to_json_dict_key(k): v for k, v in o.items()}
            else:
                new_o = o
            if isinstance(new_o, tuple):
                new_o = tuple_to_json(new_o)
            return super().encode(new_o)

        def default(self, o: object) -> object:
            """
            Convert a sage object to a JSON-compatible string.

            INPUT:

            - ``o`` -- sage object
            """
            if isinstance(o, str):
                return o
            if isinstance(
                o,
                (
                    IntegerRing_class,
                    RealField_class,
                    ComplexField_class,
                    RationalField,
                    NumberField_generic,
                ),
            ):
                return ring_to_json(o)
            if isinstance(o, (float, int, complex)):
                return o
            if isinstance(o, (Integer_t, Real_t, Complex_t, Rational, NumberFieldElement)):
                return ring_element_to_json(o)
            if isinstance(o, NumberFieldFractionalIdeal):
                return number_field_ideal_to_json(o)
            if isinstance(o, Matrix):
                return matrix_to_json(o)
            if isinstance(o, tuple):
                return tuple_to_json(o)
            if isinstance(o, Vector):
                return vector_to_json(o)
            if isinstance(o, dict):
                return dict_to_json(o)
            return super(SageJSONEncoder, self).default(o)

    class SageJSONDecoder(JSONDecoder):
        r"""
        JSON decoder for sage objects.
        """

        def __init__(self, *args: list[Any], **kwargs: dict[str, Any]) -> None:
            r"""
            Initialize the JSONDecoder.
            """
            super().__init__(*args, object_hook=self.object_hook, **kwargs)

        def object_hook(self, obj: str | dict[str, Any]) -> Any:
            """
            Convert a JSON object to a sage object.

            INPUT:

            - ``obj`` -- JSON object
            """
            return decode_function(obj)

except ImportError:  # pragma: no cover
    pass


def decode_typed_dict(obj: TypedDictType) -> Any:
    r"""
    Decode a typed dict.

    INPUT:

    - ``obj`` -- dict

    EXAMPLE::

    sage: import warnings
    sage: warnings.simplefilter("ignore")
    sage: from comp_manager.utils.json_encoder_sage import decode_typed_dict
    sage: ring = {"__type__": "ring", "name": "IntegerRing", "prec": 0}
    sage: decode_typed_dict(ring)
    Integer Ring
    sage: decode_typed_dict({"__type__": "element", "parent": ring, "value": "1"})
    1
    sage: decode_typed_dict({"__type__": "matrix", "base_ring": ring,
    ....: "entries": [["1", "2"], ["3", "4"]]})
    [1 2]
    [3 4]
    sage: decode_typed_dict({"__type__": "tuple",
    ....: "entries": ["1", "2", "3", "4"]})
    (1, 2, 3, 4)
    """
    if not isinstance(obj, dict) or "__type__" not in obj:
        raise ValueError("Invalid JSON object. Need a dict with __type__ key")
    if obj["__type__"] == "ring":
        return ring_from_json(obj)
    elif obj["__type__"] == "number_field":
        return number_field_from_json(cast(NumberFieldJson, obj))
    elif obj["__type__"] == "number_field_ideal":
        return number_field_ideal_from_json(cast(NumberFieldIdealJson, obj))
    elif obj["__type__"] == "matrix":
        return matrix_from_json(obj)
    elif obj["__type__"] == "vector":
        return vector_from_json(cast(VectorJson, obj))
    elif obj["__type__"] == "element":
        return ring_element_from_json(obj)
    elif obj["__type__"] == "tuple":
        return tuple_from_json(cast(TupleJSON, obj))
    else:
        raise ValueError(f"Invalid JSON object. Unknown type: {obj['__type__']}")


def decode_function(obj: TypedDictType | dict[str, Any] | str | bytes) -> Any:
    r"""
    Decode an object from JSON or dict.

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import decode_function
        ...
        sage: decode_function({'__type__': 'matrix',
        ....:                   'base_ring': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
        ....:                    'entries': [['1', '2'], ['3', '4']]})
        [1 2]
        [3 4]
        sage: decode_function('[1, 2, 3, 4]')
        [1, 2, 3, 4]
        sage: decode_function('{"__type__": "tuple", "entries": ["1", "2", "3", "4"]}')
        (1, 2, 3, 4)
        sage: v = decode_function({"__type__": "element",
        ....:                   "parent": {"__type__": "ring", "name": "IntegerRing", "prec": 0},
        ....:                   "value": "1"}); v
        1
        sage: type(v)
        <class 'sage.rings.integer.Integer'>
    """
    if isinstance(obj, str):
        obj = json.loads(obj)
    if isinstance(obj, bytes):
        obj = json.loads(obj.decode("utf-8"))
    if isinstance(obj, dict) and "__type__" in obj:
        return decode_typed_dict(TypedDictType(**obj))  # type: ignore[typeddict-item]
    if isinstance(obj, dict) and "_cls" in obj:
        return JSONDecoder().object_hook(obj)  # type: ignore[arg-type]
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            try:
                k_new = json.loads(k, object_hook=decode_function)
            except JSONDecodeError:
                k_new = k
            if isinstance(v, dict):
                v_new = decode_function(v)
            else:
                try:
                    v_new = json.loads(v, object_hook=decode_function)  # type: ignore[arg-type]
                except (JSONDecodeError, TypeError):
                    v_new = v
            new_dict[k_new] = v_new
        return new_dict
    if isinstance(obj, list):
        return [
            json.loads(x, object_hook=decode_function) if isinstance(x, (str, bytes)) else x
            for x in obj
        ]
    return obj


def matrix_to_json(m: Matrix) -> MatrixJson:
    """
    JSON representation of a matrix.

    EXAMPLES::
        sage: from comp_manager.utils.json_encoder_sage import matrix_to_json
        sage: m = matrix(ZZ, [[1, 2], [3, 4]])
        sage: matrix_to_json(m)
        {'__type__': 'matrix',
         'base_ring': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
         'entries': [['1', '2'], ['3', '4']]}
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: z = F.gen()
        sage: m = matrix(F, [[z^2, z^3], [z^4, z^5]])
        sage: matrix_to_json(m)
        {'__type__': 'matrix',
         'base_ring': {'__type__': 'ring',
          'field': {'__type__': 'number_field',
           'embedding': '',
           'name': 'Number Field in z with defining polynomial x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2',
           'names': ['z'],
           'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2'},
          'name': 'NumberField'},
         'entries': [['z^2', 'z^3'], ['z^4', 'z^5']]}
         sage: from comp_manager.utils.json_encoder_sage import matrix_from_json
         sage: m = matrix([[1, 2], [3, 4]])
         sage: matrix_from_json(matrix_to_json(m)) == m
         True
         sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
         sage: z = F.gen()
         sage: m = matrix(F, [[z^2, z^3], [z^4, z^5]])
         sage: matrix_from_json(matrix_to_json(m)) == m
         True
    """
    return {
        "base_ring": ring_to_json(m.base_ring()),
        "entries": [[str(x) for x in row] for row in list(m)],
        "__type__": "matrix",
    }


def vector_to_json(data: Any) -> VectorJson:
    """
    JSON representation of a vector.

    EXAMPLES::
        sage: from comp_manager.utils.json_encoder_sage import vector_to_json
        sage: vector_to_json(vector([1, 2, 3]))
        {'__type__': 'vector',
         'base_ring': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
         'entries': ['1', '2', '3']}
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: vector_to_json(vector([F.gen(), F.gen()]))
         {'__type__': 'vector',
         'base_ring': {'__type__': 'ring',
          'field': {'__type__': 'number_field',
           'embedding': '',
           'name': 'Number Field in z with defining polynomial x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2',
           'names': ['z'],
           'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2'},
          'name': 'NumberField'},
         'entries': ['z', 'z']}
    """
    return {
        "base_ring": ring_to_json(data.base_ring()),
        "entries": [str(x) for x in data],
        "__type__": "vector",
    }


def vector_from_json(data: VectorJson | Vector | dict[str, Any] | str | bytes) -> Vector:
    """
    Vector from JSON.

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import vector_from_json
        sage: vector_from_json({'__type__': 'vector',
        ....:                   'base_ring': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
        ....:                   'entries': ['1', '2', '3']})
        (1, 2, 3)
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: vector_from_json({'__type__': 'vector',
        ....:                   'base_ring': {'__type__': 'ring',
        ....:                    'field': {'__type__': 'number_field',
        ....:                    'embedding': '',
        ....:                    'name': 'Number Field in z with defining polynomial '
        ....:                           'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2',
        ....:                    'names': ['z'],
        ....:                    'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2'},
        ....:                   'name': 'NumberField'},
        ....:                   'entries': ['z', 'z']})
        (z, z)
    """
    if isinstance(data, Vector):
        return data
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, bytes):
        data = json.loads(data.decode("utf-8"))
    base_ring = ring_from_json(data["base_ring"])
    entries = [base_ring(x) for x in data["entries"]]
    return vector(base_ring, entries)


def ring_element_to_json(data: Any) -> RingElementJson:
    """
    JSON representation of a ring element.

    INPUT:

    - ``data`` -- a ring element

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import ring_element_to_json
        sage: ring_element_to_json(1)
        {'__type__': 'element',
         'parent': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
         'value': '1'}
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: ring_element_to_json(F.gen())
         {'__type__': 'element',
         'parent': {'__type__': 'ring',
          'field': {'__type__': 'number_field',
           'embedding': '',
           'name': 'Number Field in z with defining polynomial x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2',
           'names': ['z'],
           'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2'},
          'name': 'NumberField'},
          'value': 'z'}
    """
    base_ring: Ring_t = None
    # first check if we have a primitive type
    if isinstance(data, (int, float, complex)):
        base_ring = {"name": str(type(data).__name__), "prec": get_prec(data), "__type__": "ring"}
    elif isinstance(data, Integer_t):
        base_ring = {"name": "IntegerRing", "prec": get_prec(data), "__type__": "ring"}
    elif isinstance(data, Real_t):
        base_ring = {"name": "RealField", "prec": get_prec(data), "__type__": "ring"}
    elif isinstance(data, Complex_t):
        base_ring = {"name": "ComplexField", "prec": get_prec(data), "__type__": "ring"}
    elif isinstance(data, Rational):
        base_ring = {"name": "RationalField", "prec": get_prec(data), "__type__": "ring"}
    elif isinstance(data, NumberFieldElement):
        base_ring = ring_to_json(data.parent())
    if not base_ring:
        raise ValueError(f"Unsupported base ring {data}")
    return {"parent": base_ring, "value": str(data), "__type__": "element"}


def ring_element_from_json(data: RingElementJson | RingElement_t | str | bytes) -> Any:
    """
    Convert JSON representation of a ring element to a sage object.

    INPUT:

    - ``data`` -- a JSON object
    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import ring_element_from_json
        sage: ring_element_from_json({'parent': {'name': 'IntegerRing', 'prec': 0}, 'value': '1'})
        1
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: z = F.gen()
        sage: ring_element_from_json({'parent': {'field': {'names': ['z'],
        ....: 'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2',
        ....: '__type__': 'number_field'},
        ....: '__type__': 'ring',
        ....: 'name': 'NumberField'},
        ....: 'value': 'z^2'})
        z^2
    """
    if isinstance(data, RingElement_t):
        return data
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, bytes):
        data = json.loads(data.decode("utf-8"))
    parent = ring_from_json(data["parent"])
    return parent(data["value"])


def matrix_from_json(data: MatrixJson | Matrix | str | bytes) -> Matrix:
    """
    Convert JSON representation of a matrix to a sage matrix.

    Examples
    --------
        sage: from comp_manager.utils.json_encoder_sage import matrix_from_json
        sage: matrix_from_json({'base_ring': {'name': 'IntegerRing', 'prec': 0},
        ....: 'entries': [['1', '2'], ['3', '4']]})
        [1 2]
        [3 4]
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: z = F.gen()
        sage: matrix_from_json({'base_ring': {'field': {'names': ['z'],
        ....: 'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2',
        ....: '__type__': 'number_field'},
        ....: '__type__': 'ring',
        ....: 'name': 'NumberField'},
        ....: 'entries': [['z^2', 'z^3'], ['z^4', 'z^5']]})
        [z^2 z^3]
        [z^4 z^5]
    """
    if isinstance(data, Matrix):
        return data
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, bytes):
        data = json.loads(data.decode("utf-8"))
    return matrix(ring_from_json(data["base_ring"]), data["entries"])


def ring_to_json(ring: Ring_t) -> RingJson:
    """
    JSON representation of a base ring.

    Examples
    --------
        sage: from comp_manager.utils.json_encoder_sage import ring_to_json
        sage: ring_to_json(RationalField())
        {'__type__': 'ring', 'name': 'RationalField', 'prec': 0}
        sage: ring_to_json(matrix(QQ, [[1, 2], [3, 4]]).base_ring())
        {'__type__': 'ring', 'name': 'RationalField', 'prec': 0}
        sage: ring_to_json(RealField(53))
        {'__type__': 'ring', 'name': 'RealField', 'prec': 53}
        sage: ring_to_json(ComplexField(53))
        {'__type__': 'ring', 'name': 'ComplexField', 'prec': 53}
        sage: ring_to_json(ZZ)
        {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0}
        sage: ring_to_json(matrix(ZZ, [[1, 2], [3, 4]]).base_ring())
        {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0}
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: ring_to_json(F)
        {'__type__': 'ring',
         'field': {'__type__': 'number_field',
          'embedding': '',
          'name': 'Number Field in z with defining polynomial x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2',
          'names': ['z'],
          'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2'},
         'name': 'NumberField'}
    """
    if isinstance(ring, RealField_class):
        return {"name": "RealField", "prec": int(ring.prec()), "__type__": "ring"}
    if isinstance(ring, ComplexField_class):
        return {"name": "ComplexField", "prec": int(ring.prec()), "__type__": "ring"}
    if isinstance(ring, RationalField):
        return {"name": "RationalField", "prec": (0), "__type__": "ring"}
    if isinstance(ring, IntegerRing_class):
        return {"name": "IntegerRing", "prec": (0), "__type__": "ring"}
    if isinstance(ring, NumberField_generic):
        return {"name": "NumberField", "field": number_field_to_json(ring), "__type__": "ring"}
    raise ValueError(f"Unsupported base ring {ring}")


def ring_from_json(data: RingJson | Ring_t | str | bytes) -> Ring_t:
    """
    Construct ring from json data.

    INPUT:

    - ``data``: JSON data as string or dict.

    Examples
    --------
        sage: from comp_manager.utils.json_encoder_sage import ring_from_json
        sage: from comp_manager.utils.json_encoder_sage import number_field_to_json
        sage: ring_from_json({'name': 'RealField', 'prec': 53})
        Real Field with 53 bits of precision
        sage: ring_from_json({'name': 'ComplexField', 'prec': 53})
        Complex Field with 53 bits of precision
        sage: ring_from_json({'name': 'RationalField'})
        Rational Field
        sage: ring_from_json({'name': 'IntegerRing'})
        Integer Ring
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: ring_from_json({'name': 'NumberField', 'field': number_field_to_json(F)})
        Number Field in z with defining polynomial x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2
    """
    if isinstance(data, Ring_t):
        return data
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, bytes):
        data = json.loads(data.decode("utf-8"))
    fld_name = data["name"]
    allowed_functions = {"int": int, "float": float, "complex": complex}
    if fld_name in ["int", "float", "complex"]:
        return eval(fld_name, {"__builtins__": {}, **allowed_functions})  # nosec B307
    allowed_functions = {
        "RationalField": RationalField,
        "IntegerRing": IntegerRing,
        "RealField": RealField,
        "ComplexField": ComplexField,
    }
    if fld_name in ["RationalField", "IntegerRing", "RealField", "ComplexField"]:
        _cls = eval(fld_name, {"__builtins__": {}, **allowed_functions})  # nosec B307
        return _cls(data.get("prec")) if data.get("prec") else _cls()  # nosec B307
    if fld_name == "NumberField":
        if isinstance(data["field"], NumberField_generic):
            return data["field"]
        return number_field_from_json(data["field"])
    raise ValueError(f"Unsupported base ring {data}")


def number_field_to_json(nf: NumberField_generic) -> NumberFieldJson:
    """
    JSON representation of number field.

    NOTE: Any information about embeddings is ignored.

    Examples
    --------
        sage: from comp_manager.utils.json_encoder_sage import number_field_to_json
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: number_field_to_json(F)
        {'__type__': 'number_field',
         'embedding': '',
         'name': 'Number Field in z with defining polynomial x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2',
         'names': ['z'],
         'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2'}
        sage: gen = CC('-0.3122516446211537 + 1.026735437750787*I')
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z', embedding=gen)
        sage: number_field_to_json(F)
        {'__type__': 'number_field',
         'embedding': '-0.312251644621154 + 1.02673543775079*I',
         'name': 'Number Field in z with defining polynomial x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2 ...
         'names': ['z'],
         'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2'}

    """
    return {
        "polynomial": str(nf.polynomial()),
        "name": str(nf),
        "names": list(nf._names),
        "__type__": "number_field",
        "embedding": str(nf.gen_embedding().n(53)) if nf.gen_embedding() else "",
    }


def number_field_from_json(data: NumberFieldJson | str | bytes) -> NumberField_generic:
    """
    Create number field from json data.

    INPUT:

    - ``data``: JSON data as string or dict.

    Examples
    --------
        sage: from comp_manager.utils.json_encoder_sage import number_field_from_json
        sage: number_field_from_json({'polynomial': 'x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2',
        ....: 'names': ['a'], '__type__': 'number_field'})
        Number Field in a with defining polynomial x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2
        sage: from comp_manager.utils.json_encoder_sage import number_field_to_json
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z')
        sage: number_field_from_json(number_field_to_json(F)) == F
        True
        sage: gen = CC('-0.3122516446211537 + 1.026735437750787*I')
        sage: F = NumberField(x^8 + 2*x^6 + 3*x^4 + 3*x^2 + 2, 'z', embedding=gen)
        sage: number_field_from_json(number_field_to_json(F)) == F
        True

    """
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, bytes):
        data = json.loads(data.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON object. Need type {NumberFieldJson}")
    if not is_typed_dict(data, NumberFieldJson):
        raise ValueError(f"Invalid JSON object. Need type {NumberFieldJson}")
    if data["__type__"] != "number_field":
        raise ValueError(f"Invalid JSON object. Need type {NumberFieldJson}")
    emb = data.get("embedding", None)
    return NumberField(
        ZZ["x"](data["polynomial"]),
        names=tuple(data["names"]),
        embedding=ComplexField(53)(emb) if emb else None,
    )


def number_field_ideal_to_json(
    nf_ideal: NumberFieldFractionalIdeal,
) -> NumberFieldIdealJson:
    r"""
    JSON representation of a number field ideal.

    INPUT:

    - ``nf_ideal`` -- NumberFieldFractionalIdeal; the ideal to serialize

    OUTPUT:

    NumberFieldIdealJson -- JSON-compatible dict representation

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import number_field_ideal_to_json
        sage: from comp_manager.utils.json_encoder_sage import number_field_ideal_from_json
        sage: F = NumberField(x^2 + 1, 'i')
        sage: i = F.gen()
        sage: I = F.ideal(2, 1 + i)
        sage: json_data = number_field_ideal_to_json(I)
        sage: json_data['__type__']
        'number_field_ideal'
        sage: json_data['number_field']['polynomial']
        'x^2 + 1'
        sage: len(json_data['gens']) >= 1
        True
        sage: P = F.ideal(1 + i)
        sage: json_data = number_field_ideal_to_json(P)
        sage: json_data
        {'__type__': 'number_field_ideal',
         'gens': [{'__type__': 'element',
           'parent': {'__type__': 'ring',
            'field': {'__type__': 'number_field',
             'embedding': '',
             'name': 'Number Field in i with defining polynomial x^2 + 1',
             'names': ['i'],
             'polynomial': 'x^2 + 1'},
            'name': 'NumberField'},
           'value': 'i + 1'}],
         'number_field': {'__type__': 'number_field',
          'embedding': '',
          'name': 'Number Field in i with defining polynomial x^2 + 1',
          'names': ['i'],
          'polynomial': 'x^2 + 1'}}
        sage: number_field_ideal_from_json(json_data) == P
        True
    """
    if not isinstance(nf_ideal, NumberFieldFractionalIdeal):
        raise ValueError(f"Expected NumberFieldFractionalIdeal, got {type(nf_ideal)}")
    field = nf_ideal.number_field()
    gens = nf_ideal.gens_reduced()
    return {
        "__type__": "number_field_ideal",
        "number_field": number_field_to_json(field),
        "gens": [ring_element_to_json(gen) for gen in gens],
    }


def number_field_ideal_from_json(
    data: NumberFieldIdealJson | str | bytes,
) -> NumberFieldFractionalIdeal:
    r"""
    Create number field ideal from JSON data.

    INPUT:

    - ``data`` -- JSON data as string, bytes, or dict

    OUTPUT:

    NumberFieldFractionalIdeal -- the reconstructed ideal

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import (
        ....:     number_field_ideal_from_json, number_field_ideal_to_json)
        sage: F = NumberField(x^2 + 1, 'i')
        sage: i = F.gen()
        sage: I = F.ideal(2, 1 + i)
        sage: json_data = number_field_ideal_to_json(I)
        sage: reconstructed = number_field_ideal_from_json(json_data)
        sage: reconstructed == I
        True

    """
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, bytes):
        data = json.loads(data.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON object. Need type {NumberFieldIdealJson}")
    if data.get("__type__") != "number_field_ideal":
        raise ValueError(f"Invalid JSON object. Need type {NumberFieldIdealJson}")
    # Handle case where number_field has already been decoded by recursive object_hook
    nf_data = data["number_field"]
    if isinstance(nf_data, NumberField_generic):
        field = nf_data
    else:
        field = number_field_from_json(nf_data)
    # Handle case where generators have already been decoded
    gens = []
    for gen in data["gens"]:
        if isinstance(gen, NumberFieldElement):
            gens.append(gen)
        else:
            gens.append(ring_element_from_json(gen))
    return field.ideal(*gens)


def dict_from_json(data: TypedDictType | str | bytes) -> Any | dict[Any, Any]:
    """
    Transform a json dict to a python dict, which can have non-str keys.

    INPUT:

    - ``data``: JSON data as string or dict.

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import dict_from_json
        sage: dict_from_json('{"a": 1, "b": 2}')
        {'a': 1, 'b': 2}
        sage: dict_from_json('{"1": 1, "2": 2}')
        {1: 1, 2: 2}
        sage: dict_from_json('{"[1,2]": 1, "2": 2}')
        {(1, 2): 1, 2: 2}

    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, bytes):
            data = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON object.") from None
    if not isinstance(data, dict):
        raise ValueError("JSON object is not dict.")
    if "__type__" in data:
        return decode_function(data)
    new_dict = {}
    for key, value in data.items():
        try:
            new_key = json.loads(key, object_hook=decode_function)
            if isinstance(new_key, list):
                new_key = tuple(
                    [
                        json.loads(x, object_hook=decode_function) if isinstance(x, str) else x
                        for x in new_key
                    ]
                )
        except json.decoder.JSONDecodeError:
            new_key = key
        # if isinstance(value, dict):
        #     value = dict_from_json(value)
        new_dict[new_key] = decode_function(value)
    return new_dict


def to_json_dict_key(key: Any) -> str:
    r"""
    Convert a key to a JSON string.
    """
    if isinstance(key, str):
        return key
    return json.dumps(key, cls=SageJSONEncoder)


def dict_to_json(data: dict[Any, Any]) -> dict[str, Any]:
    """
    Transform a python dict to a json dict, which can only have str keys.

    INPUT:

    - ``data``: Python dict

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import dict_to_json
        sage: dict_to_json({'a': 1, 'b': 2})
        {'a': {'__type__': 'element',
          'parent': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
          'value': '1'},
         'b': {'__type__': 'element',
          'parent': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
          'value': '2'}}
        sage: dict_to_json({int(1): int(1), 2: int(2)})
        {'1': 1,
            '{"parent": {"name": "IntegerRing", "prec": 0, "__type__": "ring"},
            "value": "2", "__type__": "element"}': 2}
        sage: dict_to_json({(int(1), int(2)): int(1), int(2): 'a'})
        {'2': 'a', '{"__type__": "tuple", "entries": [1, 2]}': 1}
        sage: dict_to_json({(1, 2): 1, 2: 2})
        {'{"__type__": "tuple", "entries": [{"parent": {"name": "IntegerRing", "prec": 0,
            "__type__": "ring"}, "value": "1", "__type__": "element"},
            {"parent": {"name": "IntegerRing", "prec": 0, "__type__": "ring"}, "value": "2",
            "__type__": "element"}]}': {'__type__': 'element',
          'parent': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
          'value': '1'},
        '{"parent": {"name": "IntegerRing", "prec": 0, "__type__": "ring"}, "value": "2",
        "__type__": "element"}': {'__type__': 'element',
        'parent': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
        'value': '2'}}
        sage: from comp_manager.utils.json_encoder_sage import dict_from_json
        sage: d = {(int(1), int(2)): int(1), int(2): int(2)}
        sage: dict_from_json(dict_to_json(d)) == d
        True
        sage: d = {(1, 2): 3, 4: 5}
        sage: dict_from_json(dict_to_json(d))
        {(1, 2): 3, 4: 5}
        sage: dict_from_json(dict_to_json(d)) == d
        True

    """
    new_dict = {}
    for key, value in data.items():
        new_key = to_json_dict_key(key)
        if isinstance(value, dict):
            value = dict_to_json(value)
        else:
            value = SageJSONEncoder().default(value)
        new_dict[new_key] = value
    return new_dict


def tuple_to_json(data: tuple[Any, ...]) -> TupleJSON:
    r"""
    Transform a tuple to a json tuple.

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import tuple_to_json
        sage: from sage.all import ZZ
        sage: tuple_to_json((int(1), int(2), int(3)))
        {'__type__': 'tuple', 'entries': [1, 2, 3]}
        sage: tuple_to_json((1, 2, 3)) == tuple_to_json((ZZ(1), ZZ(2), ZZ(3)))
        True
        sage: tuple_to_json((1, 2, 3))
        {'__type__': 'tuple',
         'entries': [{'__type__': 'element',
           'parent': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
           'value': '1'},
          {'__type__': 'element',
           'parent': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
           'value': '2'},
          {'__type__': 'element',
           'parent': {'__type__': 'ring', 'name': 'IntegerRing', 'prec': 0},
           'value': '3'}]}
    """
    return {"__type__": "tuple", "entries": [SageJSONEncoder().default(x) for x in data]}


def tuple_from_json(data: TupleJSON) -> tuple[Any, ...]:
    r"""
    Transform a json tuple to a tuple.

    EXAMPLES::

        sage: from comp_manager.utils.json_encoder_sage import tuple_from_json, tuple_to_json
        sage: from sage.all import ZZ
        sage: tuple_from_json(tuple_to_json((ZZ(1), ZZ(2)))) == (ZZ(1), ZZ(2))
        True
        sage: tuple_from_json(tuple_to_json((int(1), int(2)))) == (int(1), int(2))
        True
        sage: tuple_from_json({'__type__': 'tuple', 'entries': [1, 2, 3]}) == (1, 2, 3)
        True
        sage: t = tuple_from_json({'__type__': 'tuple',
        ....: 'entries': [{'parent': {'name': 'IntegerRing', 'prec': 0, '__type__': 'ring'},
        ....: 'value': '1',
        ....: '__type__': 'element'},
        ....:   {'parent': {'name': 'IntegerRing', 'prec': 0, '__type__': 'ring'},
        ....:   'value': '2',
        ....:   '__type__': 'element'},
        ....:   {'parent': {'name': 'IntegerRing', 'prec': 0, '__type__': 'ring'},
        ....:   'value': '3',
        ....:   '__type__': 'element'}]})
        sage: t
        (1, 2, 3)
        sage: t == (ZZ(1), ZZ(2), ZZ(3))
        True
    """
    return tuple(
        [
            json.loads(x, object_hook=decode_function)
            if isinstance(x, (str, bytes))
            else decode_function(x)
            if isinstance(x, dict) and "__type__" in x
            else x
            for x in data["entries"]
        ]
    )
