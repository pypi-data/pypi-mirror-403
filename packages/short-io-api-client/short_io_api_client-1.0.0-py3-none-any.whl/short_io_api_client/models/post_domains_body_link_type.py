from enum import Enum


class PostDomainsBodyLinkType(str, Enum):
    EIGHT_CHAR = "eight-char"
    FOUR_CHAR = "four-char"
    INCREMENT = "increment"
    RANDOM = "random"
    SECURE = "secure"
    TEN_CHAR = "ten-char"

    def __str__(self) -> str:
        return str(self.value)
