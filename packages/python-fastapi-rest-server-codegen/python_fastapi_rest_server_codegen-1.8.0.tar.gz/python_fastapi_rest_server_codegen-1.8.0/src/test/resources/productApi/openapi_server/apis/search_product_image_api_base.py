# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.image import Image
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

class BaseSearchProductImageApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSearchProductImageApi.subclasses = BaseSearchProductImageApi.subclasses + (cls,)
    async def get_product_image(
        self,
        context,
        productId: int,
        imageId: int,
    ) -> Image:
        ...


    async def get_product_images(
        self,
        context,
        productId: int,
    ) -> List[Image]:
        ...
