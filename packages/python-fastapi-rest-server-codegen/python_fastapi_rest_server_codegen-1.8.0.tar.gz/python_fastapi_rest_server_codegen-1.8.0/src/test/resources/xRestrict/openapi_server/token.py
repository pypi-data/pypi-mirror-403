import jwt
import os
from fastapi import (  # noqa: F401
HTTPException
)

# Authentication constants
PUBLIC_KEY_ENV_VAR = 'LCDP_RSA_PUBLIC_KEY'
PUBLIC_KEY_HEADER = '-----BEGIN PUBLIC KEY-----\n'
PUBLIC_KEY_FOOTER = '\n-----END PUBLIC KEY-----'
PUBLIC_KEY = str.encode('{}{}{}'.format(PUBLIC_KEY_HEADER, os.getenv(PUBLIC_KEY_ENV_VAR), PUBLIC_KEY_FOOTER))
JWT_ALGORITHM = 'RS256'

# Restricted rights per end_point
fastapi_endpoint_to_restrict = {}


def decode_jwt(token):
    try:
        # TODO: Remove "verify_iat" false once https://github.com/jpadilla/pyjwt/issues/939 is fixed
        return jwt.decode(str.encode(token), PUBLIC_KEY, algorithms=JWT_ALGORITHM, options={"verify_iat": False})
    except Exception as ex:
        raise HTTPException(401, detail="Unauthorized")


def validate_roles_and_capabilities(token, end_point):
    if end_point in fastapi_endpoint_to_restrict:
        decoded_token = decode_jwt(token)

        exception_msg = "User does not have required {} for operation {}"
        expected_roles = fastapi_endpoint_to_restrict[end_point].get("roles", [])
        expected_capabilities = fastapi_endpoint_to_restrict[end_point].get("capabilities", [])
        if expected_roles and not decoded_token['role'] in expected_roles:
            raise HTTPException(403, detail=exception_msg.format("roles", end_point))

        # Using '&' operator allow to check if two set have at least one common element. (See : https://www.geeksforgeeks.org/python-check-two-lists-least-one-element-common/)
        if expected_capabilities and not (set(expected_capabilities) & set(decoded_token['capabilities'])):
            raise HTTPException(403, detail=exception_msg.format("capabilities", end_point))
