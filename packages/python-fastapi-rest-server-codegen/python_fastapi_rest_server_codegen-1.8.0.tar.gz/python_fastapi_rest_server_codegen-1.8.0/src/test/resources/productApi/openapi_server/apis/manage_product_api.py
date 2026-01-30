# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.manage_product_api_base import BaseManageProductApi
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
from openapi_server.models.product import Product
from openapi_server.models.product_creation_or_update_parameters import ProductCreationOrUpdateParameters
from openapi_server.models.rest_error import RestError
from openapi_server.models.update_vidal_package_parameters import UpdateVidalPackageParameters
from openapi_server.security_api import get_token_bearerAuth

router = APIRouter(prefix="/api/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/products",
    responses={
        200: {"model": Product, "description": "successful operation"},
        403: {"description": "Access denied"},
        409: {"description": "Product already exist"},
        4XX: {"model": RestError, "description": "Bad Request"},
    },
    tags=["ManageProduct"],
    summary="Create product from product form",
    response_model_by_alias=True,
)
async def create_product(
    request: Request,
    product_creation_or_update_parameters: ProductCreationOrUpdateParameters = Body(None, description="Product to add"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Product:
    """Required parameters for creation of vidal synchronized product :  - vidalPackageId  Required parameters for creation of product from scratch :  - name  - barcodes  - dci  - laboratoryId  - unitWeight  - vatId  - unitPrice  - typeId """
    if not BaseManageProductApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseManageProductApi.subclasses[0]().create_product(context, product_creation_or_update_parameters)


@router.put(
    "/products/{productId}/vidal-package",
    responses={
        204: {"description": "successful operation"},
        403: {"description": "Access denied"},
        404: {"description": "Product not found"},
        4XX: {"model": RestError, "description": "Bad Request"},
    },
    tags=["ManageProduct"],
    summary="Synchronize product against vidal id",
    response_model_by_alias=True,
)
async def set_product_vidal_package(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    update_vidal_package_parameters: UpdateVidalPackageParameters = Body(None, description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> None:
    if not BaseManageProductApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseManageProductApi.subclasses[0]().set_product_vidal_package(context, productId, update_vidal_package_parameters)


@router.patch(
    "/products/{productId}",
    responses={
        200: {"model": Product, "description": "successful operation"},
        400: {"model": RestError, "description": "Bad Request"},
        403: {"description": "Access denied"},
        404: {"description": "Product not found"},
        409: {"description": "Product already exist"},
    },
    tags=["ManageProduct"],
    summary="Update product from product form",
    response_model_by_alias=True,
)
async def update_product(
    request: Request,
    productId: int = Path(..., description="The id of the product concerned by the request"),
    product_creation_or_update_parameters: ProductCreationOrUpdateParameters = Body(None, description="Modifications to apply"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Product:
    """Administrator can update every fields (override allowed) Other users can only update the following fields if empty :   - unitWeight   - vat   - unitPrice   - type """
    if not BaseManageProductApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseManageProductApi.subclasses[0]().update_product(context, productId, product_creation_or_update_parameters)
