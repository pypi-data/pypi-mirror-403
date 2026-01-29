import typing
import datetime as dt
from json.decoder import JSONDecodeError

from ..core.api_error import ApiError
from ..core.client_wrapper import SyncClientWrapper
from ..core.jsonable_encoder import jsonable_encoder
from ..core.pydantic_utilities import pydantic_v1
from ..core.request_options import RequestOptions
from ..types.robots import Robot

# this is used as the default value for optional parameters
OMIT = typing.cast(typing.Any, ...)


class RobotClient:
    def __init__(self, *, client_wrapper: SyncClientWrapper):
        self._client_wrapper = client_wrapper

    def get(
        self, id: int, *, request_options: typing.Optional[RequestOptions] = None
    ) -> Robot:
        """
        Examples
        --------
        from vaapi.client import Vaapi

        client = Vaapi(
            base_url='https://vat.berlin-united.com/',
            api_key="YOUR_API_KEY",
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            f"api/robots/{jsonable_encoder(id)}/",
            method="GET",
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(Robot, _response.json())  # type: ignore
            _response_json = _response.json()

        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def delete(
        self, id: int, *, request_options: typing.Optional[RequestOptions] = None
    ) -> None:
        """
        Delete a robot.

        <Warning>This action can't be undone!</Warning>

        You will need to supply the robots unique ID. You can find the ID in
        the django admin panel..
        Parameters
        ----------
        id : int
            A unique integer value identifying this annotation.

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        None

        Examples
        --------
        from vaapi.client import Vaapi

        client = Vaapi(
            base_url='https://vat.berlin-united.com/',
            api_key="YOUR_API_KEY",
        )
        client.robots.delete(
            id=1,
        )
        """
        _response = self._client_wrapper.httpx_client.request(
            f"api/robots/{jsonable_encoder(id)}/",
            method="DELETE",
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def update(
        self,
        id: int,
        *,
        model: typing.Optional[str] = OMIT,
        head_number: typing.Optional[int] = OMIT,
        body_serial: typing.Optional[str] = OMIT,
        head_serial: typing.Optional[str] = OMIT,
        version: typing.Optional[str] = OMIT,
        purchased: typing.Optional[dt.date] = OMIT,
        warranty_end: typing.Optional[dt.date] = OMIT,
        comment: typing.Optional[str] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> Robot:
        """ """
        _response = self._client_wrapper.httpx_client.request(
            f"api/robots/{jsonable_encoder(id)}/",
            method="PATCH",
            json={
                "model": model,
                "head_number": head_number,
                "body_serial": body_serial,
                "head_serial": head_serial,
                "version": version,
                "purchased": purchased,
                "warranty_end": warranty_end,
                "comment": comment,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(Robot, _response.json())  # type: ignore
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def list(
        self,
        *,
        request_options: typing.Optional[RequestOptions] = None,
        **filters: typing.Any,
    ) -> typing.List[Robot]:
        """ """
        query_params = {k: v for k, v in filters.items() if v is not None}
        _response = self._client_wrapper.httpx_client.request(
            "api/robots/",
            method="GET",
            request_options=request_options,
            params=query_params,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(typing.List[Robot], _response.json())  # type: ignore
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def create(
        self,
        *,
        model: typing.Optional[str] = OMIT,
        head_number: typing.Optional[int] = OMIT,
        body_serial: typing.Optional[str] = OMIT,
        head_serial: typing.Optional[str] = OMIT,
        version: typing.Optional[str] = OMIT,
        purchased: typing.Optional[dt.date] = OMIT,
        warranty_end: typing.Optional[dt.date] = OMIT,
        comment: typing.Optional[str] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> Robot:
        """ """
        _response = self._client_wrapper.httpx_client.request(
            "api/robots/",
            method="POST",
            json={
                "model": model,
                "head_number": head_number,
                "body_serial": body_serial,
                "head_serial": head_serial,
                "version": version,
                "purchased": purchased,
                "warranty_end": warranty_end,
                "comment": comment,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(Robot, _response.json())  # type: ignore
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)
