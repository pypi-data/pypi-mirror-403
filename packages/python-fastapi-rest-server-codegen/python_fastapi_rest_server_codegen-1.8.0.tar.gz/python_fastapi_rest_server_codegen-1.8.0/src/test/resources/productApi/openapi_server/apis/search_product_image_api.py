# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.search_product_image_api_base import BaseSearchProductImageApi
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
from openapi_server.models.image import Image
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

router = APIRouter(prefix="/api/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/products/{productId}/images/{imageId}",
    responses={
        200: {"model": Image, "description": "successful operation"},
        403: {"description": "Access denied"},
        404: {"description": "Product not found"},
        4XX: {"model": RestError, "description": "Bad Request"},
    },
    tags=["SearchProductImage"],
    summary="Return product&#39;s images",
    response_model_by_alias=True,
)
async def get_product_image(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    imageId: int = Path(..., description="The id of the product image concerned by the request"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Image:
    if not BaseSearchProductImageApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseSearchProductImageApi.subclasses[0]().get_product_image(context, productId, imageId)


@router.get(
    "/products/{productId}/images",
    responses={
        200: {"model": List[Image], "description": "successful operation"},
        403: {"description": "Access denied"},
        404: {"description": "Product not found"},
        4XX: {"model": RestError, "description": "Bad Request"},
    },
    tags=["SearchProductImage"],
    summary="Return product&#39;s images",
    response_model_by_alias=True,
)
async def get_product_images(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> List[Image]:
    if not BaseSearchProductImageApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseSearchProductImageApi.subclasses[0]().get_product_images(context, productId)
