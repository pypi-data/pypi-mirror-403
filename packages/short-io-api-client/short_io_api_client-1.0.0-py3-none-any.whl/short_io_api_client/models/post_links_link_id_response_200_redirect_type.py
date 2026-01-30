from enum import Enum


class PostLinksLinkIdResponse200RedirectType(str, Enum):
    VALUE_0 = "301"
    VALUE_1 = "302"
    VALUE_2 = "307"
    VALUE_3 = "308"

    def __str__(self) -> str:
        return str(self.value)
