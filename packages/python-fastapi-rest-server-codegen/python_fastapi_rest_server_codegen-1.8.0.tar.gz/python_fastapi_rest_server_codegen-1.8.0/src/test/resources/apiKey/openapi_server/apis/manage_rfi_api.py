# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.manage_rfi_api_base import BaseManageRfiApi
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
from openapi_server.security_api import get_token_apiKeyAuth, get_token_captchaApiKey, get_token_bearerAuth

router = APIRouter(prefix="/api/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/rfis",
    responses={
        204: {"description": "Message sent"},
        404: {"description": "Order not found"},
    },
    tags=["ManageRfi"],
    summary="Contact form",
    response_model_by_alias=True,
)
async def create_rfi(
    request: Request,
    token_apiKeyAuth: TokenModel = Security(
        get_token_apiKeyAuth
    ),
    token_captchaApiKey: TokenModel = Security(
        get_token_captchaApiKey
    ),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> None:
    if not BaseManageRfiApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, token_apiKeyAuth=token_apiKeyAuth,token_captchaApiKey=token_captchaApiKey,token_bearerAuth=token_bearerAuth,)
    return await BaseManageRfiApi.subclasses[0]().create_rfi(context, )
