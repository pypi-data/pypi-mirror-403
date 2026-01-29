from typing import Type, Any, TypeVar, Union, Protocol, cast, runtime_checkable

T = TypeVar('T')
V = TypeVar('V', covariant=True)


@runtime_checkable
class _ConstSpaceType(Protocol[V]):
    @classmethod
    def __getattr__(cls, name: str) -> V: ...

ConstSpaceType = Union[_ConstSpaceType[Any], Any]


class _ConstSpaceMeta(type):
    def __setattr__(cls, name: str, value: Any):
        raise AttributeError(f'''ConstSpace '{cls.__name__}' is read-only.''')

    def __delattr__(cls, name: str):
        raise AttributeError(f'''ConstSpace '{cls.__name__}' is read-only.''')

    def __repr__(cls):
        consts = [k for k in cls.__dict__ if not k.startswith('_')]
        return f"<ConstSpace {cls.__name__}: {', '.join(consts)}>"


class ConstSpace(metaclass=_ConstSpaceMeta):
    '''Base class for identity grouping.'''
    pass


def constspace(cls: Type[T]) -> Type[T]:
    '''
    The 'constspace' decorator.
    Usage:
        @constspace
        class MyConfig:
            TOKEN = "123"
    '''
    bases = (ConstSpace,) + tuple(b for b in cls.__bases__ if b is not object)
    cls_dict = dict(cls.__dict__)
    
    def __init__(self: Any):
        raise TypeError(f'''ConstSpace '{cls.__name__}' cannot be instantiated.''')
    
    cls_dict['__init__'] = __init__
    
    return cast(Type[T], _ConstSpaceMeta(cls.__name__, bases, cls_dict))