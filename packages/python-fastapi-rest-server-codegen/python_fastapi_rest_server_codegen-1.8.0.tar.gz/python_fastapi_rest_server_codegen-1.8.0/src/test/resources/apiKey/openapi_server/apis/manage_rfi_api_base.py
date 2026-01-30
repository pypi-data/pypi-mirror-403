# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.security_api import get_token_apiKeyAuth, get_token_captchaApiKey, get_token_bearerAuth

class BaseManageRfiApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseManageRfiApi.subclasses = BaseManageRfiApi.subclasses + (cls,)
    async def create_rfi(
        self,
        context,
    ) -> None:
        ...
