# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.manage_product_image_api_base import BaseManageProductImageApi
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
from openapi_server.security_api import get_token_bearerAuth

router = APIRouter(prefix="/api/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/products/{productId}/images",
    responses={
        204: {"description": "successful operation"},
        404: {"description": "No product found"},
        403: {"description": "Bad request"},
        413: {"description": "Image too large maximum allowed is 10 MB"},
        415: {"description": "Wrong media type"},
    },
    tags=["ManageProductImage"],
    summary="Upload one or more images",
    response_model_by_alias=True,
)
async def create_product_image(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    images: List[file] = Form(None, description="File to upload related to image type (Max 10 Mo)"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> None:
    if not BaseManageProductImageApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseManageProductImageApi.subclasses[0]().create_product_image(context, productId, images)


@router.delete(
    "/products/{productId}/images/{imageId}",
    responses={
        204: {"description": "successful operation"},
        404: {"description": "No product found"},
        403: {"description": "Access denied"},
        4XX: {"description": "Bad Request"},
    },
    tags=["ManageProductImage"],
    summary="Remove product&#39;s image",
    response_model_by_alias=True,
)
async def delete_product_image(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    imageId: int = Path(..., description="The id of the product image concerned by the request"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> None:
    if not BaseManageProductImageApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseManageProductImageApi.subclasses[0]().delete_product_image(context, productId, imageId)
