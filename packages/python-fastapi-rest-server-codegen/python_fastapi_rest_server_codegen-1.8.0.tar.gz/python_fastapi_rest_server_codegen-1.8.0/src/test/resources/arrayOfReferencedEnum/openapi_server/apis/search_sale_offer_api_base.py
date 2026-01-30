# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.sale_offer_status import SaleOfferStatus


class BaseSearchSaleOfferApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSearchSaleOfferApi.subclasses = BaseSearchSaleOfferApi.subclasses + (cls,)
    async def get_sale_offers(
        self,
        context,
        st_eq: List[SaleOfferStatus],
    ) -> str:
        """"""
        ...


    async def get_sale_offers_by_status(
        self,
        context,
        saleOfferStatus: ,
    ) -> None:
        ...
