import ctypes
import inspect
from typing import Sequence, Any, Literal

from _hydrogenlib_core.typefunc import iter_annotations, alias
from ._special_methods import _bind_py_type

short = _bind_py_type(int, ctypes.c_short)
ushort = _bind_py_type(int, ctypes.c_ushort)
long = _bind_py_type(int, ctypes.c_long)
longlong = _bind_py_type(int, ctypes.c_longlong)
ulonglong = _bind_py_type(int, ctypes.c_ulonglong)
double = _bind_py_type(float, ctypes.c_double)
byte = _bind_py_type(int, ctypes.c_byte)
ubyte = _bind_py_type(int, ctypes.c_ubyte)


def struct(name: str, fields: Sequence[tuple[str, Any]], endian='big') -> type[ctypes.Structure]:
    base = ctypes.Structure
    match endian:
        case 'little':
            base = ctypes.LittleEndianStructure
        case 'big':
            base = ctypes.BigEndianStructure
        case _:
            raise ValueError(f"Bad endianness {endian}")

    return type(
        name, (base,), {
            '_fields_': tuple(fields)
        }
    )


def union(name: str, fields: Sequence[tuple[str, Any]], endian='big') -> type[ctypes.Union]:
    base = ctypes.Union
    match endian:
        case 'little':
            base = ctypes.LittleEndianUnion
        case 'big':
            base = ctypes.BigEndianUnion
        case _:
            raise ValueError(f"Bad endianness {endian}")

    return type(
        name, (base,), {
            '_fields_': tuple(fields)
        }
    )


class _Ctype:
    __ctype__ = None
    __real_ctype__ = None

    def __init__(self, ctype):
        self.__ctype__ = ctype

    def __class_getitem__(cls, item):
        return cls(
            cls.__real_ctype__(cls.as_ctype(item))) if not isinstance(item, tuple) \
            else cls(cls.__real_ctype__(*map(cls.as_ctype, item)))

    @classmethod
    def as_ctype(cls, obj):
        if isinstance(obj, type):
            if issubclass(obj, str):
                return ctypes.c_wchar_p
            elif issubclass(obj, int):
                return ctypes.c_int
            elif issubclass(obj, bytes | bytearray):
                return ctypes.c_char_p

        while isinstance(obj, cls) or (isinstance(obj, type) and issubclass(obj, _Cobj)):
            obj = obj.__ctype__
        return obj

    def __getattr__(self, item):
        return getattr(self.__ctype__, item)


class _Cobj:
    __cobj__ = None
    __ctype__ = None

    @classmethod
    def as_cobj(cls, obj):
        while isinstance(obj, cls):
            obj = obj.__cobj__
        return obj

    def __getattr__(self, item):
        return getattr(self.__cobj__, item)

    @property
    def _as_parameter_(self):
        return self.__cobj__


class Pointer(_Ctype):  # Pointer Type
    __real_ctype__ = ctypes.POINTER


class Array(_Ctype):
    __real_ctype__ = ctypes.ARRAY


class Struct(_Ctype):
    @staticmethod
    def __real_ctype__(*field_types):
        fields = []
        for x, ftype in enumerate(field_types):
            fields.append(
                (f"Field_{x}", ftype)
            )

        return struct('', *fields)


class StructBase(_Cobj):
    def __init_subclass__(cls, **kwargs):
        cls.__ctype__ = struct(
            cls.__name__,
            [(name, _Ctype.as_ctype(anno)) for name, anno, value in iter_annotations(cls)],
            endian=kwargs.get('endian', 'big')
        )

    def __init__(self, *args, **kwargs):
        self.__cobj__ = self.__ctype__(
            *args, **kwargs
        )

    def get_pointer(self):
        return ctypes.pointer(_Cobj.as_cobj(self))

    def get_ref(self, offset=0):
        return ctypes.byref(_Cobj.as_cobj(self), offset)


class UnionBase(_Cobj, _Ctype):
    def __init_subclass__(cls, **kwargs):
        cls.__ctype__ = union(
            cls.__name__,
            [(name, _Ctype.as_ctype(anno)) for name, anno, value in iter_annotations(cls)],
            endian=kwargs.get('endian', 'big')
        )

    def __init__(self, *args, **kwargs):
        super().__init__(self.__ctype__)
        self.__cobj__ = self.__ctype__(
            *args, **kwargs
        )


class Prototype(_Ctype):
    __class_getitem__ = None

    def __init__(self, restype, *argtypes, ftype: Literal['c', 'py', 'win'] = 'c', signature=None):
        ftype = {
            'c': ctypes.CFUNCTYPE,
            'win': ctypes.WINFUNCTYPE,
            'py': ctypes.PYFUNCTYPE
        }[ftype]

        super().__init__(
            ftype(
                _Ctype.as_ctype(restype), *map(_Ctype.as_ctype, argtypes)
            )
        )

        self._signature = signature

    @property
    def signature(self):
        if self._signature is None:
            self._signature = self._generate_signature()
        return self._signature

    def __call__(self, *args, **kwargs):
        return FuncPtr(self.__ctype__(*args, **kwargs))

    @classmethod
    def from_pyfunc(cls, func, ftype: str = 'c'):
        signature = inspect.signature(func)

        restype = signature.return_annotation

        if restype is signature.empty:
            restype = None

        argtypes = [
            param.annotation
            for param in signature.parameters.values()
        ]

        return cls(restype, *argtypes, ftype=ftype, signature=signature)


class FuncPtr(_Cobj):  # TODO: complete me!
    _funcptr = alias['__cobj__']

    def __init__(self, ptr, prototype=None):
        self._funcptr = ptr
        self._prototype = prototype

    def __call__(self, *args, **kwargs):
        return self._funcptr(*args, **kwargs)
