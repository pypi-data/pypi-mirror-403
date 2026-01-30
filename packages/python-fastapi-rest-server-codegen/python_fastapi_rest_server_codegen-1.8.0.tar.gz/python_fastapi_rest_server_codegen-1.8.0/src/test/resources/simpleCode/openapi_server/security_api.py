# coding: utf-8

from typing import List

from fastapi import Depends, HTTPException, Request, Security  # noqa: F401
from fastapi.openapi.models import OAuthFlowImplicit, OAuthFlows  # noqa: F401
from fastapi.security import (  # noqa: F401
HTTPAuthorizationCredentials,
HTTPBasic,
HTTPBasicCredentials,
HTTPBearer,
OAuth2,
OAuth2AuthorizationCodeBearer,
OAuth2PasswordBearer,
SecurityScopes,
)
from fastapi.security.api_key import APIKeyCookie, APIKeyHeader, APIKeyQuery  # noqa: F401

from openapi_server.models.extra_models import TokenModel

from openapi_server.token import decode_jwt, validate_roles_and_capabilities

