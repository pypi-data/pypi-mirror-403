# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from openapi_server.apis.notification_api_base import BaseNotificationApi
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
from openapi_server.models.notification_sending import NotificationSending


router = APIRouter(prefix="/v1")

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/notification",
    responses={
        200: {"model": List[NotificationSending], "description": "successful operation"},
        400: {"description": "Invalid ID supplied"},
        403: {"description": "Access denied"},
        405: {"description": "User not found"},
    },
    tags=["notification"],
    summary="Request all notifications",
    response_model_by_alias=True,
)
async def get_notifications(
    request: Request,
    authorization: str = Header(None, description=""),
    number: int = Query(None, description="Number of notifications", alias="number", ge=1, le=10),
    page: int = Query(None, description="Page number to search for", alias="page", ge=1, le=10),
) -> List[NotificationSending]:
    """"""
    if not BaseNotificationApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    context = create_context(request, )
    return await BaseNotificationApi.subclasses[0]().get_notifications(context, authorization, number, page)
