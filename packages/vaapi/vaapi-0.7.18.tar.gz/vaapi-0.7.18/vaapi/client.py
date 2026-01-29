from .base_client import VaapiBase


class Vaapi(VaapiBase):
    """"""

    __doc__ += VaapiBase.__doc__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class VATClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key
