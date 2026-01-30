# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.search_sale_offer_api_base import BaseSearchSaleOfferApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    Security,
    status,
)
from openapi_server.context import create_context
from typing import Optional

from openapi_server.models.extra_models import TokenModel  # noqa: F401
from openapi_server.models.sale_offer_status import SaleOfferStatus


router = APIRouter(prefix="/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/sale-offers",
    responses={
        200: {"model": str, "description": "Session id created"},
        405: {"description": "Invalid input"},
    },
    tags=["searchSaleOffer"],
    summary="Search sale offers",
    response_model_by_alias=True,
)
async def get_sale_offers(
    request: Request,
    st_eq: List[SaleOfferStatus] = Query(None, description="Filter on status to include in the search (can be given multiple time which result in a OR condition)", alias="st[eq]"),
) -> str:
    """"""
    if not BaseSearchSaleOfferApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BaseSearchSaleOfferApi.subclasses[0]().get_sale_offers(context, st_eq)


@router.get(
    "/sale-offers/{saleOfferStatus}",
    responses={
        200: {"description": "Success"},
        403: {"description": "Access denied"},
        400: {"description": "Bad Request"},
    },
    tags=["searchSaleOffer"],
    summary="Search sale offers by status",
    response_model_by_alias=True,
)
async def get_sale_offers_by_status(
    request: Request,
    saleOfferStatus:  = Path(..., description=""),
) -> None:
    if not BaseSearchSaleOfferApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BaseSearchSaleOfferApi.subclasses[0]().get_sale_offers_by_status(context, saleOfferStatus)
