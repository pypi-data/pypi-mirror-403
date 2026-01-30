from enum import Enum


class GetDomainsDomainIdResponse200UserPlan(str, Enum):
    HOBBY = "hobby"
    LARGE = "large"
    SMALL = "small"
    STANDARD = "standard"
    TINY = "tiny"

    def __str__(self) -> str:
        return str(self.value)
