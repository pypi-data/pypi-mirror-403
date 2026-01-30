# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.paginated_products import PaginatedProducts
from openapi_server.models.product import Product
from openapi_server.models.product_status import ProductStatus
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

class BaseSearchProductApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSearchProductApi.subclasses = BaseSearchProductApi.subclasses + (cls,)
    async def get_product(
        self,
        context,
        productId: int,
    ) -> Product:
        ...


    async def get_products(
        self,
        context,
        q: str,
        vidal_package_eq: int,
        st_eq: List[ProductStatus],
        pt_eq: str,
        spt_eq: str,
        lab_eq: List[int],
        s_waiting_sale_offer_count_gte: int,
        order_by: str,
        p: int,
        pp: int,
    ) -> PaginatedProducts:
        ...


    async def test_free_access(
        self,
        context,
    ) -> None:
        ...
