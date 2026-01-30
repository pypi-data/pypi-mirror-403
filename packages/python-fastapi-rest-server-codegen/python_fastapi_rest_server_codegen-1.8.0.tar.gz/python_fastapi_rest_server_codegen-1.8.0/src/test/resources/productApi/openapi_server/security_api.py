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


bearer_auth = HTTPBearer()


def get_token_bearerAuth(request: Request, credentials: HTTPAuthorizationCredentials = Depends(bearer_auth)) -> TokenModel:
    """
    Check and retrieve authentication information from custom bearer token.

    :param credentials Credentials provided by Authorization header
    :type credentials: HTTPAuthorizationCredentials
    :return: Decoded token information or None if token is invalid
    :rtype: TokenModel | None
    """

    validate_roles_and_capabilities(credentials.credentials, request.scope.get('route').name)

    try:
        # Return decoded token
        return decode_jwt(credentials.credentials)
    except Exception as ex:
        raise HTTPException(401, str(ex))

