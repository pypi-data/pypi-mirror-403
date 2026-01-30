# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.product_secondary_type import ProductSecondaryType
from openapi_server.models.product_type import ProductType
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

class BaseSearchProductMetadataApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSearchProductMetadataApi.subclasses = BaseSearchProductMetadataApi.subclasses + (cls,)
    async def get_product_secondary_types(
        self,
        context,
    ) -> List[ProductSecondaryType]:
        ...


    async def get_product_types(
        self,
        context,
    ) -> List[ProductType]:
        ...
