from enum import Enum


class GetDomainsDomainIdResponse200HttpsLevel(str, Enum):
    HSTS = "hsts"
    NONE = "none"
    REDIRECT = "redirect"

    def __str__(self) -> str:
        return str(self.value)
