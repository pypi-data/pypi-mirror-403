# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.search_product_proscription_api_base import BaseSearchProductProscriptionApi
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
from openapi_server.models.paginated_product_proscriptions import PaginatedProductProscriptions
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

router = APIRouter(prefix="/api/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/products/{productId}/proscriptions",
    responses={
        200: {"model": PaginatedProductProscriptions, "description": "successful operation"},
        400: {"model": RestError, "description": "Bad Request"},
        403: {"description": "Access denied"},
        404: {"description": "Product not found"},
    },
    tags=["SearchProductProscription"],
    summary="Get product proscriptions",
    response_model_by_alias=True,
)
async def get_product_proscriptions(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    order_by: str = Query('BATCH:asc', description="Sort by", alias="orderBy"),
    p: int = Query(None, description="Page number to search for (start at 0)", alias="p", ge=0),
    pp: int = Query(None, description="Number of proscriptions per page", alias="pp", ge=1, le=50),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> PaginatedProductProscriptions:
    if not BaseSearchProductProscriptionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseSearchProductProscriptionApi.subclasses[0]().get_product_proscriptions(context, productId, order_by, p, pp)
