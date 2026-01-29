from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T", bound="Cover")


@dataclass
class Cover:
    type: str
    external_url: str | None = None

    def __init__(self, type: str, external_url: str | None = None) -> None:
        self.type = type
        self.external_url = external_url

    @classmethod
    def of(cls: type[T], param: dict) -> T:
        return cls(
            type=param["type"],
            external_url=param["external"]["url"] if "external" in param else None,
        )

    @classmethod
    def from_external_url(cls: type[T], external_url: str) -> T:
        return cls(
            type="external",
            external_url=external_url,
        )

    def __dict__(self) -> dict:
        result: dict[str, Any] = {
            "type": self.type,
        }
        if self.external_url is not None:
            result["external"] = {
                "url": self.external_url,
            }
        return result
