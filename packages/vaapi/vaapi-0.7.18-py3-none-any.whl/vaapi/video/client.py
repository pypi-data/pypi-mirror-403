import typing
from json.decoder import JSONDecodeError

from ..core.api_error import ApiError
from ..core.client_wrapper import SyncClientWrapper
from ..core.jsonable_encoder import jsonable_encoder
from ..core.pydantic_utilities import pydantic_v1
from ..core.request_options import RequestOptions
from pathlib import Path
from ..types.video import Video

# this is used as the default value for optional parameters
OMIT = typing.cast(typing.Any, ...)


class VideoClient:
    def __init__(self, *, client_wrapper: SyncClientWrapper):
        self._client_wrapper = client_wrapper

    def get(
        self, id: int, *, request_options: typing.Optional[RequestOptions] = None
    ) -> Video:
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
            f"api/video/{jsonable_encoder(id)}/",
            method="GET",
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(Video, _response.json())  # type: ignore
            _response_json = _response.json()

        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def delete(
        self, id: int, *, request_options: typing.Optional[RequestOptions] = None
    ) -> None:
        _response = self._client_wrapper.httpx_client.request(
            f"api/video/{jsonable_encoder(id)}/",
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
        game: typing.Optional[str] = OMIT,
        experiment: typing.Optional[str] = OMIT,
        video_path: typing.Optional[str] = OMIT,
        url: typing.Optional[str] = OMIT,
        type: typing.Optional[str] = OMIT,
        comment: typing.Optional[str] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> Video:
        """ """
        _response = self._client_wrapper.httpx_client.request(
            f"api/video/{jsonable_encoder(id)}/",
            method="PATCH",
            json={
                "game": game,
                "experiment": experiment,
                "video_path": video_path,
                "url": url,
                "type": type,
                "comment": comment,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(Video, _response.json())  # type: ignore
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def list(
        self,
        *,
        # game_id: typing.Optional[int] = None,
        request_options: typing.Optional[RequestOptions] = None,
        **filters: typing.Any,
    ) -> typing.List[Video]:
        query_params = {k: v for k, v in filters.items() if v is not None}

        _response = self._client_wrapper.httpx_client.request(
            "api/video/",
            method="GET",
            request_options=request_options,
            params=query_params,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(typing.List[Video], _response.json())  # type: ignore
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def create(
        self,
        *,
        game: typing.Optional[str] = OMIT,
        experiment: typing.Optional[str] = OMIT,
        video_path: typing.Optional[str] = OMIT,
        url: typing.Optional[str] = OMIT,
        type: typing.Optional[str] = OMIT,
        comment: typing.Optional[str] = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> Video:
        """ """
        _response = self._client_wrapper.httpx_client.request(
            "api/video/",
            method="POST",
            json={
                "game": game,
                "experiment": experiment,
                "video_path": video_path,
                "url": url,
                "type": type,
                "comment": comment,
            },
            request_options=request_options,
            omit=OMIT,
        )
        try:
            if 200 <= _response.status_code < 300:
                return pydantic_v1.parse_obj_as(Video, _response.json())  # type: ignore
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def slice(
        self,
        *,
        game: int,
        start: int,
        end: int,
        request_options: typing.Optional[RequestOptions] = None
    ) -> Video:
        """
        Examples
        --------
        from vaapi.client import Vaapi

        client = Vaapi(
            base_url='https://vat.berlin-united.com/',
            api_key="YOUR_API_KEY",
        )
        """

        query_params = {
            "game": game,
            "start": start,
            "end": end,
        }

        with self._client_wrapper.httpx_client.stream(
            "api/video/slice",
            method="GET",
            request_options=request_options,
            params=query_params,
        ) as r:
            if r.status_code >= 400:
                # Read the error body (often JSON) if the status code indicates an error
                try:
                    r.read()
                    error_details = r.json()  # Tries to parse the body as JSON
                except JSONDecodeError:
                    error_details = r.read()  # Reads body as raw bytes/text if not JSON

                # You can raise an exception or handle the error
                print(f"ERROR: Received status code {r.status_code} - {error_details}")

                # Depending on your desired flow, you might want to 'return' or 'raise' here
                return
            print(r.headers)
            content_disposition = r.headers.get("Content-Disposition")
            if content_disposition:
                # Example: attachment; filename="1a2b3c4d.mp4"
                filename = Path(content_disposition.split("filename=")[-1].strip('"')).name
                print(filename)
                with open(str(filename), 'wb') as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
            else:
                with open("test4.mp4", 'wb') as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
