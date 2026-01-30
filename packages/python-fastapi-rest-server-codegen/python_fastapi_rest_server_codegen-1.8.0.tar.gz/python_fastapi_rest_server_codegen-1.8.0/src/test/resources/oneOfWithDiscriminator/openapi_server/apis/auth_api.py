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
from openapi_server.models.any_authentication_credential import AnyAuthenticationCredential


router = APIRouter(prefix="/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/token",
    responses={
        200: {"description": "Session created"},
    },
    tags=["auth"],
    summary="Create a new session",
    response_model_by_alias=True,
)
async def login(
    request: Request,
    any_authentication_credential: AnyAuthenticationCredential = Body(None, description="Credentials to use in order to create the session"),
) -> None:
    """"""
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BaseAuthApi.subclasses[0]().login(context, any_authentication_credential)
