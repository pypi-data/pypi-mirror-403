import datetime as dt
import typing
from ..core.datetime_utils import serialize_datetime
from ..core.pydantic_utilities import deep_union_pydantic_dicts, pydantic_v1
from .cognition_frame import CognitionFrame

class Image(pydantic_v1.BaseModel):
    #: Id assigned by django
    id: typing.Optional[int] = None

    # 1. READ Field: The full object (what the server returns)
    # This should be the official field name in your model.
    frame: typing.Optional[CognitionFrame] = None 
    
    # 2. WRITE Field: The integer ID (what you send or use internally)
    # We use an alias ONLY IF the API requires the JSON key to be 'frame'
    frame_id_on_write: typing.Optional[int] = None

    #: camera
    camera: typing.Optional[str] = None

    #: type
    type: typing.Optional[str] = None

    #: image_url
    image_url: typing.Optional[str] = pydantic_v1.Field(default=None)

    #: blurredness_value
    blurredness_value: typing.Optional[int] = pydantic_v1.Field(default=None)

    brightness_value: typing.Optional[int] = pydantic_v1.Field(default=None)

    labelstudio_url: typing.Optional[str] = pydantic_v1.Field(default=None)

    validated: typing.Optional[bool] = pydantic_v1.Field(default=None)

    @pydantic_v1.root_validator(pre=True)
    def handle_read_write_difference(cls, values):
        frame_data = values.get('frame')
        
        # If it's a dict, it's a READ response, let Pydantic validate against CognitionFrame
        if isinstance(frame_data, dict):

            return values
        
        # If it's an int, it's a WRITE input, set the ID field and remove the 'frame' key
        # so it doesn't try to parse an int as a CognitionFrame object.
        elif isinstance(frame_data, int):
            values['frame_id_on_write'] = frame_data
            del values['frame'] 
        
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

    class Config:
        frozen = True
        smart_union = True
        extra = pydantic_v1.Extra.allow
        json_encoders = {dt.datetime: serialize_datetime}
        fields = {
            'frame_id_on_write': {
                'exclude': True, # exclude from .dict() and .json()
                'repr': False    # exclude from the model's string representation (print)
            }
        }


class ImageOffsetPagination(pydantic_v1.BaseModel):
    """
    Offset/limit paginated response for tasks
    """
    results: typing.List[Image]
    count: int
    next: typing.Any
    previous: typing.Any
    
    class Config:
        frozen = True
        smart_union = True
        extra = pydantic_v1.Extra.allow