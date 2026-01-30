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
from openapi_server.models.credential import Credential


router = APIRouter(prefix="/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/session",
    responses={
        200: {"model": str, "description": "Session id created"},
        405: {"description": "Invalid input"},
    },
    tags=["auth"],
    summary="Create a new session",
    response_model_by_alias=True,
)
async def login(
    request: Request,
    credential: Credential = Body(None, description="Credentials to use in order to create the session"),
) -> str:
    """"""
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BaseAuthApi.subclasses[0]().login(context, credential)


@router.delete(
    "/session/{sessionId}",
    responses={
        400: {"description": "Invalid ID supplied"},
        404: {"description": "User not found"},
    },
    tags=["auth"],
    summary="Delete an existing session",
    response_model_by_alias=True,
)
async def logout(
    request: Request,
    sessionId: int = Path(..., description="Session id to delete"),
    authorization: str = Header(None, description=""),
) -> None:
    """"""
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BaseAuthApi.subclasses[0]().logout(context, sessionId, authorization)
