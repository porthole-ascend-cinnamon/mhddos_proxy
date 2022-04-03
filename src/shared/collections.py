from enum import Enum as _Enum
from typing import Any


class Enum(_Enum):
    def __add__(self, other: "Enum") -> list:
        return self.list() + other.list()

    def __iadd__(self, other: "Enum") -> list:
        return self.__add__(other)

    @classmethod
    def list(cls) -> list[Any]:
        """Returns the list of values."""
        return [item.value for item in cls]
