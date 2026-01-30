# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.product import Product
from openapi_server.models.product_creation_or_update_parameters import ProductCreationOrUpdateParameters
from openapi_server.models.rest_error import RestError
from openapi_server.models.update_vidal_package_parameters import UpdateVidalPackageParameters
from openapi_server.security_api import get_token_bearerAuth

class BaseManageProductApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseManageProductApi.subclasses = BaseManageProductApi.subclasses + (cls,)
    async def create_product(
        self,
        context,
        product_creation_or_update_parameters: ProductCreationOrUpdateParameters,
    ) -> Product:
        """Required parameters for creation of vidal synchronized product :  - vidalPackageId  Required parameters for creation of product from scratch :  - name  - barcodes  - dci  - laboratoryId  - unitWeight  - vatId  - unitPrice  - typeId """
        ...


    async def set_product_vidal_package(
        self,
        context,
        productId: int,
        update_vidal_package_parameters: UpdateVidalPackageParameters,
    ) -> None:
        ...


    async def update_product(
        self,
        context,
        productId: int,
        product_creation_or_update_parameters: ProductCreationOrUpdateParameters,
    ) -> Product:
        """Administrator can update every fields (override allowed) Other users can only update the following fields if empty :   - unitWeight   - vat   - unitPrice   - type """
        ...
