from enum import Enum


class GetDomainsDomainIdResponse403Type(str, Enum):
    ACCESSDENIED = "accessDenied"

    def __str__(self) -> str:
        return str(self.value)
