from enum import Enum


class PostLinksQrLinkIdStringBodyType(str, Enum):
    PNG = "png"
    SVG = "svg"

    def __str__(self) -> str:
        return str(self.value)
