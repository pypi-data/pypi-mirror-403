# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.pets_api_base import BasePetsApi
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
from openapi_server.models.error import Error
from openapi_server.models.pet import Pet


router = APIRouter(prefix="/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/pets",
    responses={
        201: {"description": "Null response"},
        200: {"model": Error, "description": "unexpected error"},
    },
    tags=["pets"],
    summary="Create a pet",
    response_model_by_alias=True,
)
async def create_pets(
    request: Request,
) -> None:
    if not BasePetsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BasePetsApi.subclasses[0]().create_pets(context, )


@router.get(
    "/pets",
    responses={
        200: {"model": List[Pet], "description": "A paged array of pets"},
        200: {"model": Error, "description": "unexpected error"},
    },
    tags=["pets"],
    summary="List all pets",
    response_model_by_alias=True,
)
async def list_pets(
    request: Request,
    limit: int = Query(None, description="How many items to return at one time (max 100)", alias="limit"),
) -> List[Pet]:
    if not BasePetsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BasePetsApi.subclasses[0]().list_pets(context, limit)


@router.get(
    "/pets/{petId}",
    responses={
        200: {"model": Pet, "description": "Expected response to a valid request"},
        200: {"model": Error, "description": "unexpected error"},
    },
    tags=["pets"],
    summary="Info for a specific pet",
    response_model_by_alias=True,
)
async def show_pet_by_id(
    request: Request,
    petId: str = Path(..., description="The id of the pet to retrieve"),
) -> Pet:
    if not BasePetsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BasePetsApi.subclasses[0]().show_pet_by_id(context, petId)
