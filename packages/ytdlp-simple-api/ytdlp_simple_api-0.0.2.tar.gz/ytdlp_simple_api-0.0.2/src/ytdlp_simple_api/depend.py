from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ytdlp_simple_api.config import API_TOKEN

_bearer_scheme = HTTPBearer(auto_error=False)


async def verify_token(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> None:
    """
    validate Bearer token from Authorization header.

    if API_TOKEN env is not set, authentication is disabled (open access).

    Usage:
        @app.post("/endpoint", dependencies=[Depends(verify_token)])
        async def endpoint(): ...

    Header format:
        Authorization: Bearer <token>
    """
    if not API_TOKEN:
        return

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
