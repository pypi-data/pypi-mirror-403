# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.auth_api_base import BaseAuthApi
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

router = APIRouter(prefix="/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.delete(
    "/route",
    responses={
        400: {"description": "Invalid ID supplied"},
        404: {"description": "User not found"},
    },
    tags=["auth"],
    summary="Delete route",
    response_model_by_alias=True,
)
async def delete_route(
    request: Request,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> None:
    """"""
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseAuthApi.subclasses[0]().delete_route(context, )


@router.get(
    "/route",
    responses={
        200: {"model": str, "description": "Session id created"},
        405: {"description": "Invalid input"},
    },
    tags=["auth"],
    summary="Get route",
    response_model_by_alias=True,
)
async def get_route(
    request: Request,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> str:
    """"""
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseAuthApi.subclasses[0]().get_route(context, )


@router.post(
    "/route",
    responses={
        200: {"model": str, "description": "Session id created"},
        405: {"description": "Invalid input"},
    },
    tags=["auth"],
    summary="Create route",
    response_model_by_alias=True,
)
async def post_route(
    request: Request,
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> str:
    """"""
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_bearerAuth=token_bearerAuth,)
    return await BaseAuthApi.subclasses[0]().post_route(context, )
