from enum import Enum


class GetDomainsDomainIdResponse200State(str, Enum):
    CONFIGURED = "configured"
    EXTRA_RECORDS = "extra_records"
    NOT_CONFIGURED = "not_configured"
    NOT_REGISTERED = "not_registered"
    NOT_VERIFIED = "not_verified"
    REGISTRATION_PENDING = "registration_pending"

    def __str__(self) -> str:
        return str(self.value)
