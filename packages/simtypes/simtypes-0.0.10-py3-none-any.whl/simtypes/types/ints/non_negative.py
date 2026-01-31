from typing import Any


class NonNegativeIntMeta(type):
    def __instancecheck__(cls, instance: Any) -> bool:
        return isinstance(instance, int) and instance >= 0

class NonNegativeInt(metaclass=NonNegativeIntMeta):
    pass
