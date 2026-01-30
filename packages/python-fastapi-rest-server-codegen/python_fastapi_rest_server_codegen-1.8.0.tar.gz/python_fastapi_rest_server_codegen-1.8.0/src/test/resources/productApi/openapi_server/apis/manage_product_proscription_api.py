# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.manage_product_proscription_api_base import BaseManageProductProscriptionApi
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
from openapi_server.models.product_proscription import ProductProscription
from openapi_server.models.product_proscription_creation_parameters import ProductProscriptionCreationParameters
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

router = APIRouter(prefix="/api/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/products/{productId}/proscriptions",
    responses={
        200: {"model": ProductProscription, "description": "successful operation"},
        400: {"model": RestError, "description": "Bad Request"},
        403: {"description": "Access denied"},
        404: {"description": "Product or Batch not found"},
        409: {"description": "Proscription already exist"},
    },
    tags=["ManageProductProscription"],
    summary="Create a product proscription",
    response_model_by_alias=True,
)
async def create_product_proscription(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    product_proscription_creation_parameters: ProductProscriptionCreationParameters = Body(None, description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ProductProscription:
    """**! WARNING !** this method can change the status of one or more sales-offers """
    if not BaseManageProductProscriptionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseManageProductProscriptionApi.subclasses[0]().create_product_proscription(context, productId, product_proscription_creation_parameters)


@router.delete(
    "/products/{productId}/proscriptions/{proscriptionId}",
    responses={
        204: {"description": "successful operation"},
        400: {"model": RestError, "description": "Bad Request"},
        403: {"description": "Access denied"},
        404: {"description": "Product or Proscription Id not found"},
    },
    tags=["ManageProductProscription"],
    summary="Delete this product proscription",
    response_model_by_alias=True,
)
async def delete_product_proscription(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    proscriptionId: int = Path(..., description="The id of the product proscription"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> None:
    if not BaseManageProductProscriptionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseManageProductProscriptionApi.subclasses[0]().delete_product_proscription(context, productId, proscriptionId)
