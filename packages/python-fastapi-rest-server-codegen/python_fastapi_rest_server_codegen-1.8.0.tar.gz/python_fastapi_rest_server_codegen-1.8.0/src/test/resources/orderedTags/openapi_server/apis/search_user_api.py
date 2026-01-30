# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.search_user_api_base import BaseSearchUserApi
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


router = APIRouter(prefix="/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/users/{userId}",
    responses={
        200: {"description": "successful operation"},
        404: {"description": "User not found"},
    },
    tags=["searchUser"],
    summary="Retrieve one user",
    response_model_by_alias=True,
)
async def get_user(
    request: Request,
    userId: int = Path(..., description="The id of the user concerned by the request"),
) -> None:
    """"""
    if not BaseSearchUserApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BaseSearchUserApi.subclasses[0]().get_user(context, userId)
