# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.search_product_metadata_api_base import BaseSearchProductMetadataApi
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
from openapi_server.models.product_secondary_type import ProductSecondaryType
from openapi_server.models.product_type import ProductType
from openapi_server.models.rest_error import RestError
from openapi_server.security_api import get_token_bearerAuth

router = APIRouter(prefix="/api/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/products/secondary-types",
    responses={
        200: {"model": List[ProductSecondaryType], "description": "Product&#39;s types found"},
        403: {"description": "Access denied"},
        4XX: {"model": RestError, "description": "Bad Request"},
    },
    tags=["SearchProductMetadata"],
    summary="Get product secondary types",
    response_model_by_alias=True,
)
async def get_product_secondary_types(
    request: Request,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> List[ProductSecondaryType]:
    if not BaseSearchProductMetadataApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseSearchProductMetadataApi.subclasses[0]().get_product_secondary_types(context, )


@router.get(
    "/products/types",
    responses={
        200: {"model": List[ProductType], "description": "Product&#39;s types found"},
        403: {"description": "Access denied"},
        4XX: {"model": RestError, "description": "Bad Request"},
    },
    tags=["SearchProductMetadata"],
    summary="Get product types",
    response_model_by_alias=True,
)
async def get_product_types(
    request: Request,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> List[ProductType]:
    if not BaseSearchProductMetadataApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseSearchProductMetadataApi.subclasses[0]().get_product_types(context, )
