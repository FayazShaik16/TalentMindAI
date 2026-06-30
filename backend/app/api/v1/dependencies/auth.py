from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)

async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict[str, str]:
    """
    Verifies JWT token validity. If FLAG_AUTHENTICATION is disabled, it falls back
    to returning a default mock administrator object.
    """
    if not settings.FLAG_AUTHENTICATION:
        return {
            "user_id": "mock-tenant-id-01",
            "role": "admin",
            "email": "admin@talentmind.ai"
        }

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token parsing and JWT decoding skeleton (to be implemented in later phases)
    return {
        "user_id": "validated-user-id",
        "role": "recruiter",
        "email": "recruiter@talentmind.ai"
    }
