# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.default_api_base import BaseDefaultApi
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
from openapi_server.models.any_mode import AnyMode


router = APIRouter(prefix="")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/modes",
    responses={
        200: {"model": AnyMode, "description": "successful operation"},
    },
    tags=["default"],
    response_model_by_alias=True,
)
async def get_mode(
    request: Request,
) -> AnyMode:
    if not BaseDefaultApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BaseDefaultApi.subclasses[0]().get_mode(context, )
