from enum import Enum


class PostDomainsSettingsDomainIdBodyRobots(str, Enum):
    ALLOW = "allow"
    DISALLOW = "disallow"
    NOINDEX = "noindex"

    def __str__(self) -> str:
        return str(self.value)
