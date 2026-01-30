# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.any_authentication_credential import AnyAuthenticationCredential


class BaseAuthApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAuthApi.subclasses = BaseAuthApi.subclasses + (cls,)
    async def login(
        self,
        context,
        any_authentication_credential: AnyAuthenticationCredential,
    ) -> None:
        """"""
        ...
