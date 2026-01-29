from typing import Any, Union, TypeVar, Protocol, cast, runtime_checkable


T = TypeVar('T', bound=type)
V = TypeVar('V', covariant=True)

@runtime_checkable
class _ConstSpaceType(Protocol[V]):
    @classmethod
    def __getattr__(cls, name: str) -> V: ...


ConstSpaceType = Union[_ConstSpaceType[Any], Any]


class _ConstSpaceMeta(type):
    '''
    Metaclass that enforces read-only behavior and custom error messages.
    Implements the runtime side of ConstSpaceType.
    '''
    def __getattr__(cls, name: str) -> Any:
        raise AttributeError(f'''ConstSpace '{cls.__name__}' has no attribute '{name}'.''')

    def __setattr__(cls, name: str, value: Any) -> None:
        raise AttributeError(f'''ConstSpace '{cls.__name__}' is read-only.''')

    def __delattr__(cls, name: str) -> None:
        raise AttributeError(f'''ConstSpace '{cls.__name__}' is read-only.''')

    def __repr__(cls) -> str:
        consts = [k for k in cls.__dict__ if not k.startswith('_')]
        return f'<ConstSpace {cls.__name__}: {', '.join(consts)}>'


def constspace(cls: T) -> T:
    '''
    The 'constspace' decorator for creating immutable namespaces.
    Supports recursive nesting and is Pylance strict-mode compliant.
    '''
    # Prepare the dictionary for the new class
    cls_dict = dict(cls.__dict__)
    
    # Recursively process nested classes
    for name, value in cls_dict.items():
        if isinstance(value, type) and not name.startswith('__'):
            if not isinstance(value, _ConstSpaceMeta):
                cls_dict[name] = constspace(value)

    # Prevent instantiation
    def __init__(self: Any) -> None:
        raise TypeError(f'''ConstSpace '{cls.__name__}' cannot be instantiated.''')
    
    cls_dict['__init__'] = __init__

    # Construct new bases & new class
    new_bases = cls.__bases__ if cls.__bases__ != (object,) else (object,)
    new_cls = _ConstSpaceMeta(cls.__name__, new_bases, cls_dict)
    
    return cast(T, new_cls)