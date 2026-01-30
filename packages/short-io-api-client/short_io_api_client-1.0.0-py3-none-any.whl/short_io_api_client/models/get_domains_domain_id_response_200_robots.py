from enum import Enum


class GetDomainsDomainIdResponse200Robots(str, Enum):
    ALLOW = "allow"
    DISALLOW = "disallow"
    NOINDEX = "noindex"

    def __str__(self) -> str:
        return str(self.value)
