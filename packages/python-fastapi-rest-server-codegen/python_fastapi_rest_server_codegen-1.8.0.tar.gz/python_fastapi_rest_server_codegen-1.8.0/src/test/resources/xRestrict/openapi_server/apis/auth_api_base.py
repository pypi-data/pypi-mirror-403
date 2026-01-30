# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.security_api import get_token_bearerAuth

class BaseAuthApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAuthApi.subclasses = BaseAuthApi.subclasses + (cls,)
    async def delete_route(
        self,
        context,
    ) -> None:
        """"""
        ...


    async def get_route(
        self,
        context,
    ) -> str:
        """"""
        ...


    async def post_route(
        self,
        context,
    ) -> str:
        """"""
        ...
