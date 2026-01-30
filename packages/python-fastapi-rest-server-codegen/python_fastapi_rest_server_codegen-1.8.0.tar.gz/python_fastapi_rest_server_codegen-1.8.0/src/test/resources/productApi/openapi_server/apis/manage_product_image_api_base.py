# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.security_api import get_token_bearerAuth

class BaseManageProductImageApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseManageProductImageApi.subclasses = BaseManageProductImageApi.subclasses + (cls,)
    async def create_product_image(
        self,
        context,
        productId: int,
        images: List[file],
    ) -> None:
        ...


    async def delete_product_image(
        self,
        context,
        productId: int,
        imageId: int,
    ) -> None:
        ...
