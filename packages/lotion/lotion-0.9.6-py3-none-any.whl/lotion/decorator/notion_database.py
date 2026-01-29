import types
from typing import Any, TypeVar, Union, cast, get_args, get_origin

from ..properties.checkbox import Checkbox
from ..properties.date import Date
from ..properties.email import Email
from ..properties.multi_select import MultiSelect
from ..properties.phone_number import PhoneNumber
from ..properties.property import Property
from ..properties.relation import Relation
from ..properties.select import Select
from ..properties.status import Status
from ..properties.text import Text
from ..properties.title import Title
from ..properties.url import Url

P = TypeVar("P", bound=Property)


def __extract_type_from_union(type_hint: type[P]) -> type[P]:
    """Extract the actual type from Union types like X | None or Optional[X]."""
    origin = get_origin(type_hint)
    # Python 3.10+ uses types.UnionType for X | None syntax
    # typing.Union is used for Optional[X] or Union[X, None]
    if origin is Union or isinstance(type_hint, types.UnionType):
        args = [arg for arg in get_args(type_hint) if arg is not type(None)]
        if args:
            return args[0]
    return type_hint


def __cast(value: Property, cls: type[P]) -> P:
    # Handle Union types (X | None or Optional[X])
    cls = __extract_type_from_union(cls)
    parent_class = cls.__bases__[0]
    if isinstance(value, Title) and parent_class == Title:
        return cls(
            name=value.name,
            rich_text=value.rich_text,
            id=value.id,
        )
    if isinstance(value, Text) and parent_class == Text:
        return cls(
            name=value.name,
            id=value.id,
            rich_text=value.rich_text,
        )
    if isinstance(value, Checkbox) and parent_class == Checkbox:
        return cls(
            name=value.name,
            checked=value.checked,
            id=value.id,
        )
    if isinstance(value, Date) and parent_class == Date:
        return cls(
            name=value.name,
            id=value.id,
            start=value.start,
            end=value.end,
            time_zone=value.time_zone,
        )
    if isinstance(value, Email) and parent_class == Email:
        return cls(
            name=value.name,
            value=value.value,
            id=value.id,
        )
    if isinstance(value, PhoneNumber) and parent_class == PhoneNumber:
        return cls(
            name=value.name,
            value=value.value,
            id=value.id,
        )
    if isinstance(value, MultiSelect) and parent_class == MultiSelect:
        return cls(
            name=value.name,
            values=value.values,
            id=value.id,
        )
    if isinstance(value, Relation) and parent_class == Relation:
        return cls(
            name=value.name,
            id=value.id,
            id_list=value.id_list,
            has_more=value.has_more,
        )
    if isinstance(value, Select) and parent_class == Select:
        return cls(
            name=value.name,
            id=value.id,
            selected_name=value.selected_name,
            selected_id=value.selected_id,
            selected_color=value.selected_color,
        )
    if isinstance(value, Status) and parent_class == Status:
        return cls(
            name=value.name,
            id=value.id,
            status_name=value.status_name,
            status_id=value.status_id,
            status_color=value.status_color,
        )
    if isinstance(value, Url) and parent_class == Url:
        return cls(
            name=value.name,
            id=value.id,
            url=value.url,
        )
    return cast(P, value)


def notion_database(database_id: str):
    """
    クラスデコレータ: データベースIDを引数として受け取り、
    自動的に BasePage を継承させ、アノテーションの属性をプロパティ化する。
    """

    def decorator(cls):
        # 元の初期化をオーバーライドしてアノテーション属性をプロパティ化
        original_init = getattr(cls, "__init__", lambda _: None)

        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)

            # クラスアノテーションに基づいてプロパティを設定
            for attr_name, attr_type in cls.__annotations__.items():

                def make_getter(typ: type[P]):
                    def getter(self) -> Any:
                        # print(typ, name)  # デバッグ出力
                        result = self.get_prop(typ)  # `self.get()` は任意の実装
                        return __cast(result, typ)

                    return getter

                def make_setter(name, typ):
                    def setter(self, value: Any):
                        # Extract actual type from Union types for isinstance check
                        actual_type = __extract_type_from_union(typ)
                        if not isinstance(value, actual_type):
                            raise TypeError(f"Expected {actual_type} for {name}, got {type(value)}")
                        # print(f"Setting {name} of type {typ} to {value}")  # デバッグ出力
                        self.set_prop(value)  # `set` メソッドを直接呼び出す

                    return setter

                # プロパティを作成してクラスに設定
                setattr(cls, attr_name, property(make_getter(attr_type), make_setter(attr_name, attr_type)))

        # デコレータ引数で渡された database_id をクラス属性として設定
        cls.DATABASE_ID = database_id

        cls.__init__ = new_init
        cls.__module__ = cls.__module__

        return cls

    return decorator
