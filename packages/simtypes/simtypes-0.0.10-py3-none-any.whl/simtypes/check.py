from inspect import isclass
from unittest.mock import Mock, MagicMock

try:
    from types import UnionType  # type: ignore[attr-defined, unused-ignore]
except ImportError:  # pragma: no cover
    from typing import Union as UnionType  # type: ignore[assignment, unused-ignore]

try:
    from typing import TypeIs  # type: ignore[attr-defined, unused-ignore]
except ImportError:  # pragma: no cover
    from typing_extensions import TypeIs

from typing import List, Type, Union, Any, get_args, get_origin

from denial import InnerNoneType

from simtypes.typing import ExpectedType


def check(value: Any, type_hint: Type[ExpectedType], strict: bool = False, lists_are_tuples: bool = False, pass_mocks: bool = True) -> TypeIs[ExpectedType]:
    if type_hint is Any:  # type: ignore[comparison-overlap]
        return True

    elif (isinstance(value, Mock) or isinstance(value, MagicMock)) and pass_mocks:
        return True

    elif type_hint is None:
        return value is None

    elif isinstance(type_hint, InnerNoneType):
        return type_hint == value

    origin_type = get_origin(type_hint)

    if origin_type is Union or origin_type is UnionType:
        return any(check(value, argument, strict=strict, lists_are_tuples=lists_are_tuples) for argument in get_args(type_hint))

    elif origin_type is list and strict:
        if not isinstance(value, list):
            return False
        arguments = get_args(type_hint)
        if not arguments:
            return True
        return all(check(subvalue, arguments[0], strict=strict, lists_are_tuples=lists_are_tuples) for subvalue in value)

    elif origin_type is dict and strict:
        if not isinstance(value, dict):
            return False
        arguments = get_args(type_hint)
        if not arguments:
            return True
        return all(check(key, arguments[0], strict=strict, lists_are_tuples=lists_are_tuples) and check(subvalue, arguments[1], strict=strict, lists_are_tuples=lists_are_tuples) for key, subvalue in value.items())

    elif origin_type is tuple and strict:
        types_to_check: List[Union[Type[list], Type[tuple]]] = [tuple] if not lists_are_tuples else [tuple, list]  # type: ignore[type-arg]
        if all(not isinstance(value, x) for x in types_to_check):
            return False

        arguments = get_args(type_hint)

        if not arguments:
            return True

        if len(arguments) == 2 and arguments[1] is Ellipsis:
            return all(check(subvalue, arguments[0], strict=strict, lists_are_tuples=lists_are_tuples) for subvalue in value)

        if len(arguments) != len(value):
            return False

        return all(check(subvalue, expected_subtype, strict=strict, lists_are_tuples=lists_are_tuples) for subvalue, expected_subtype in zip(value, arguments))

    else:
        if origin_type is not None:
            return isinstance(value, origin_type)

        if not isclass(type_hint):
            raise ValueError('Type must be a valid type object.')

        if type_hint is tuple and lists_are_tuples:
            return isinstance(value, tuple) or isinstance(value, list)  # pragma: no cover

        return isinstance(value, type_hint)
