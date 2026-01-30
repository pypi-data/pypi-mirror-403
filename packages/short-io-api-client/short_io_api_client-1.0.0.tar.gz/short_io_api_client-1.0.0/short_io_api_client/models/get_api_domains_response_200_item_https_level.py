from enum import Enum


class GetApiDomainsResponse200ItemHttpsLevel(str, Enum):
    HSTS = "hsts"
    NONE = "none"
    REDIRECT = "redirect"

    def __str__(self) -> str:
        return str(self.value)
