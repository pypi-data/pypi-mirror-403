from enum import Enum


class GetLinksExpandResponse200Source(str, Enum):
    API = "api"
    PUBLIC = "public"
    SLACK = "slack"
    SPREADSHEETS = "spreadsheets"
    TELEGRAM = "telegram"
    VALUE_6 = ""
    WEBSITE = "website"

    def __str__(self) -> str:
        return str(self.value)
