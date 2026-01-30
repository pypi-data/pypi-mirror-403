# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.paginated_product_proscriptions import PaginatedProductProscriptions
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

class BaseSearchProductProscriptionApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSearchProductProscriptionApi.subclasses = BaseSearchProductProscriptionApi.subclasses + (cls,)
    async def get_product_proscriptions(
        self,
        context,
        productId: int,
        order_by: str,
        p: int,
        pp: int,
    ) -> PaginatedProductProscriptions:
        ...
