# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.search_product_api_base import BaseSearchProductApi
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
from openapi_server.models.paginated_products import PaginatedProducts
from openapi_server.models.product import Product
from openapi_server.models.product_status import ProductStatus
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

router = APIRouter(prefix="/api/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/products/{productId}",
    responses={
        200: {"model": Product, "description": "Product found"},
        400: {"model": RestError, "description": "Bad Request"},
        403: {"description": "Access denied"},
        404: {"description": "Product not found"},
    },
    tags=["SearchProduct"],
    summary="Retrieve a product with ID",
    response_model_by_alias=True,
)
async def get_product(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Product:
    if not BaseSearchProductApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseSearchProductApi.subclasses[0]().get_product(context, productId)


@router.get(
    "/products",
    responses={
        200: {"model": PaginatedProducts, "description": "Product&#39;s list found"},
        403: {"description": "Access denied"},
        4XX: {"model": RestError, "description": "Bad Request"},
    },
    tags=["SearchProduct"],
    summary="Search for products with his name or status",
    response_model_by_alias=True,
)
async def get_products(
    request: Request,
    q: str = Query(None, description="Any field in the product contains &#39;q&#39;", alias="q"),
    vidal_package_eq: int = Query(None, description="Vidal package equal this one", alias="vidalPackage[eq]"),
    st_eq: List[ProductStatus] = Query(None, description="Filter on status to include in the search (can be given multiple time which result in a OR condition)", alias="st[eq]"),
    pt_eq: str = Query(None, description="Product type to search on", alias="pt[eq]"),
    spt_eq: str = Query(None, description="Secondary product type to search on", alias="spt[eq]"),
    lab_eq: List[int] = Query(None, description="Laboratory to search on (can be given multiple time which result in a OR condition)", alias="lab[eq]"),
    s_waiting_sale_offer_count_gte: int = Query(None, description="Waiting sale offers count greater than or equal", alias="sWaitingSaleOfferCount[gte]"),
    order_by: str = Query('CREATED_AT:desc', description="Sort by", alias="orderBy"),
    p: int = Query(None, description="Page number to search for (start at 0)", alias="p", ge=0),
    pp: int = Query(None, description="Number of user per page", alias="pp", ge=1, le=50),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> PaginatedProducts:
    if not BaseSearchProductApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseSearchProductApi.subclasses[0]().get_products(context, q, vidal_package_eq, st_eq, pt_eq, spt_eq, lab_eq, s_waiting_sale_offer_count_gte, order_by, p, pp)


@router.get(
    "/products/testFreeAccess",
    responses={
        200: {"description": "Success"},
        403: {"description": "Access denied"},
    },
    tags=["SearchProduct"],
    summary="Test generation without bearer",
    response_model_by_alias=True,
)
async def test_free_access(
    request: Request,
) -> None:
    if not BaseSearchProductApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BaseSearchProductApi.subclasses[0]().test_free_access(context, )
