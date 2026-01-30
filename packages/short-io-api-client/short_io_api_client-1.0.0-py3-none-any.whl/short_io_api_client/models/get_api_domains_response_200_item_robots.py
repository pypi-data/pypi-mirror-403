from enum import Enum


class GetApiDomainsResponse200ItemRobots(str, Enum):
    ALLOW = "allow"
    DISALLOW = "disallow"
    NOINDEX = "noindex"

    def __str__(self) -> str:
        return str(self.value)
