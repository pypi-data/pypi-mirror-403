from enum import Enum


class PostDomainsResponse200HttpsLevel(str, Enum):
    HSTS = "hsts"
    NONE = "none"
    REDIRECT = "redirect"

    def __str__(self) -> str:
        return str(self.value)
