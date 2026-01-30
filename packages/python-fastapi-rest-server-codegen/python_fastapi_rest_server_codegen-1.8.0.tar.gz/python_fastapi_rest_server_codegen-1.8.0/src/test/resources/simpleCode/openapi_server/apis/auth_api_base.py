# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.credential import Credential


class BaseAuthApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAuthApi.subclasses = BaseAuthApi.subclasses + (cls,)
    async def login(
        self,
        context,
        credential: Credential,
    ) -> str:
        """"""
        ...


    async def logout(
        self,
        context,
        sessionId: int,
        authorization: str,
    ) -> None:
        """"""
        ...
