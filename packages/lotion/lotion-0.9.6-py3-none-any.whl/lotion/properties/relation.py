from dataclasses import dataclass
from typing import Any, TypeVar

from .prop import Prop
from .property import Property

T = TypeVar("T", bound="Relation")


@dataclass
class Relation(Property):
    id_list: list[str]
    has_more: bool = False

    TYPE = "relation"

    def __init__(
        self,
        name: str,
        id: str | None = None,
        id_list: list[str] | None = None,
        has_more: bool | None = None,
    ) -> None:
        self.name = name
        self.id = id
        self.id_list = list(set(id_list)) if id_list else []
        self.has_more = bool(has_more)

    @classmethod
    def of(cls: type[T], name: str, property: dict[str, Any]) -> T:
        id_list = [r["id"] for r in property["relation"]]
        return cls(name=name, id_list=id_list, has_more=property["has_more"])

    @classmethod
    def from_id_list(cls: type[T], id_list: list[str], name: str | None = None) -> T:
        return cls(
            name=name or cls.PROP_NAME,
            id_list=id_list,
        )

    @classmethod
    def from_id(cls: type[T], id: str, name: str | None = None) -> T:
        return cls.from_id_list(name=name or cls.PROP_NAME, id_list=[id])

    def append(self, id: str) -> None:
        self.id_list.append(id)

    def __dict__(self) -> dict:
        result = {
            "type": self.TYPE,
            "relation": [
                {
                    "id": id,
                }
                for id in self.id_list
            ],
            "has_more": self.has_more,
        }
        if self.id is not None:
            result["relation"]["id"] = self.id
        return {
            self.name: result,
        }

    @property
    def _prop_type(self) -> Prop:
        return Prop.RELATION

    @property
    def _value_for_filter(self) -> Any:
        if len(self.id_list) > 1:
            raise ValueError(f"{self.name}: Relation property can only have one value for filter.")
        return self.id_list[0]
