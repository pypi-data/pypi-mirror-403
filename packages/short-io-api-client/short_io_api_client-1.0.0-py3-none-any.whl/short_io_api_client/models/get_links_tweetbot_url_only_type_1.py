from enum import Enum


class GetLinksTweetbotUrlOnlyType1(str, Enum):
    VALUE_0 = "0"

    def __str__(self) -> str:
        return str(self.value)
