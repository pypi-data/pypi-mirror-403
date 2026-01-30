# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.product_proscription import ProductProscription
from openapi_server.models.product_proscription_creation_parameters import ProductProscriptionCreationParameters
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

class BaseManageProductProscriptionApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseManageProductProscriptionApi.subclasses = BaseManageProductProscriptionApi.subclasses + (cls,)
    async def create_product_proscription(
        self,
        context,
        productId: int,
        product_proscription_creation_parameters: ProductProscriptionCreationParameters,
    ) -> ProductProscription:
        """**! WARNING !** this method can change the status of one or more sales-offers """
        ...


    async def delete_product_proscription(
        self,
        context,
        productId: int,
        proscriptionId: int,
    ) -> None:
        ...
