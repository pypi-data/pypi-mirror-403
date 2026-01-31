from typing import Callable, Dict, Any, Optional

import jwt
from async_lru import alru_cache
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, Cookie
from fastapi import Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWK

from sirius.common import is_test_environment, get_environmental_secret
from sirius.constants import SiriusEnvironmentSecretKey
from sirius.exceptions import ApplicationException


async def get_private_key() -> str:
    generate_private_key: Callable[[], str] = lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")

    if is_test_environment():
        return generate_private_key()

    try:
        return await get_environmental_secret(SiriusEnvironmentSecretKey.PRIVATE_KEY)
    except ApplicationException:
        return await get_environmental_secret(SiriusEnvironmentSecretKey.PRIVATE_KEY, generate_private_key())


@alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
async def get_public_key() -> str:
    private_key_string: str = await get_private_key()
    return (serialization.load_pem_private_key(private_key_string.encode("utf-8"), password=None)
            .public_key()
            .public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode("utf-8"))


@alru_cache(maxsize=50, ttl=86_400)  # 24 hour cache
async def get_jwks_client(oidc_config_url: str) -> jwt.PyJWKClient:
    from sirius.http_requests import AsyncHTTPSession
    oidc_config: Dict[str, Any] = (await AsyncHTTPSession(oidc_config_url).get(oidc_config_url)).data
    return jwt.PyJWKClient(oidc_config.get("jwks_uri"))


async def is_token_valid(token: str, oidc_config_url: str | None = None, audience: str | None = None, issuer: str | None = None) -> bool:
    if not token:
        return False

    tenant_id: str = await get_environmental_secret(SiriusEnvironmentSecretKey.MICROSOFT_TENANT_ID)
    audience = await get_environmental_secret(SiriusEnvironmentSecretKey.MICROSOFT_CLIENT_ID) if not audience else audience
    issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0" if not issuer else issuer
    oidc_config_url = f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration" if not oidc_config_url else oidc_config_url
    jwks_client = await get_jwks_client(oidc_config_url)

    try:
        signing_key: PyJWK = jwks_client.get_signing_key(jwt.get_unverified_header(token)["kid"])
        jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            verify=True
        )
    except Exception:
        return False

    return True


async def verify_token(header_token: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)), cookie_token: Optional[str] = Cookie(None, alias="Authorization")) -> None:
    pass
    # token: str | None = cookie_token.replace("Bearer ", "") if cookie_token else header_token.credentials if header_token else None
    # if not await is_token_valid(token):
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}, )


async def redirect_unauthorized_handler(request: Request, exc: HTTPException) -> Response:
    # login_url: str = await get_environmental_secret(SiriusEnvironmentSecretKey.LOGIN_REDIRECT_URI, "http://localhost:9000/token")
    # return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)
    raise exc
