import datetime as dt
import typing

from ..core.datetime_utils import serialize_datetime
from ..core.pydantic_utilities import deep_union_pydantic_dicts, pydantic_v1


class Timeline(pydantic_v1.BaseModel):
    # Id assigned by django
    id: typing.Optional[int] = None

    robot: typing.Optional[int] = pydantic_v1.Field(default=None)

    status: typing.Optional[str] = pydantic_v1.Field(default=None)

    description: typing.Optional[str] = pydantic_v1.Field(default=None)

    created: typing.Optional[dt.datetime] = pydantic_v1.Field(default=None)

    modified: typing.Optional[dt.datetime] = pydantic_v1.Field(default=None)

    def json(self, **kwargs: typing.Any) -> str:
        kwargs_with_defaults: typing.Any = {
            "by_alias": True,
            "exclude_unset": True,
            **kwargs,
        }
        return super().json(**kwargs_with_defaults)

    def dict(self, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]:
        kwargs_with_defaults_exclude_unset: typing.Any = {
            "by_alias": True,
            "exclude_unset": True,
            **kwargs,
        }
        kwargs_with_defaults_exclude_none: typing.Any = {
            "by_alias": True,
            "exclude_none": True,
            **kwargs,
        }

        return deep_union_pydantic_dicts(
            super().dict(**kwargs_with_defaults_exclude_unset),
            super().dict(**kwargs_with_defaults_exclude_none),
        )

    class Config:
        frozen = True
        smart_union = True
        extra = pydantic_v1.Extra.allow
        json_encoders = {dt.datetime: serialize_datetime}
