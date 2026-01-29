import datetime as dt
import typing

from ..core.datetime_utils import serialize_datetime
from ..core.pydantic_utilities import deep_union_pydantic_dicts, pydantic_v1
from .robots import Robot

class Log(pydantic_v1.BaseModel):
    #: Id assigned by django
    id: typing.Optional[int] = None

    #: Foreign key to the game this log is from
    game: typing.Optional[int] = None

    # Foreign key to the experiment this log is from
    experiment: typing.Optional[int] = None

    robot: typing.Optional[Robot] = None
    robot_id_on_write: typing.Optional[int] = None

    player_number: typing.Optional[int] = None


    representation_list: typing.Optional[typing.Dict[str, typing.Any]] = (
        pydantic_v1.Field(default=None)
    )

    sensor_log_path: typing.Optional[str] = pydantic_v1.Field(default=None)

    log_path: typing.Optional[str] = pydantic_v1.Field(default=None)

    combined_log_path: typing.Optional[str] = pydantic_v1.Field(default=None)

    git_commit: typing.Optional[str] = pydantic_v1.Field(default=None)

    is_favourite: typing.Optional[bool] = pydantic_v1.Field(default=None)

    @pydantic_v1.root_validator(pre=True)
    def handle_read_write_difference(cls, values):
        robot_data = values.get('robot')
        
        # If it's a dict, it's a READ response, let Pydantic validate against CognitionFrame
        if isinstance(robot_data, dict):

            return values
        
        # If it's an int, it's a WRITE input, set the ID field and remove the 'frame' key
        # so it doesn't try to parse an int as a CognitionFrame object.
        elif isinstance(robot_data, int):
            values['robot_id_on_write'] = robot_data
            del values['robot'] 
        
        return values

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

    def __str__(self):
        return f"{self.id} - {self.log_path}"

    class Config:
        frozen = True
        smart_union = True
        extra = pydantic_v1.Extra.allow
        json_encoders = {dt.datetime: serialize_datetime}
