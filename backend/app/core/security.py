"""
Security utilities for Clerk authentication
"""
import jwt
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings


security = HTTPBearer()


class ClerkAuthError(Exception):
    """Custom exception for Clerk authentication errors"""
    pass


class ClerkAuth:
    """Clerk authentication handler"""

    def __init__(self):
        self.secret_key = settings.CLERK_SECRET_KEY
        self.issuer = settings.CLERK_JWT_ISSUER
        self.jwks_cache: Optional[Dict[str, Any]] = None

    async def get_jwks(self) -> Dict[str, Any]:
        """Get JWKS from Clerk"""
        if not self.jwks_cache:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.issuer}/.well-known/jwks.json")
                if response.status_code == 200:
                    self.jwks_cache = response.json()
                else:
                    raise ClerkAuthError("Failed to fetch JWKS")
        return self.jwks_cache

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token from Clerk"""
        try:
            # Decode token header to get kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise ClerkAuthError("Token missing 'kid' in header")

            # Get JWKS and find the right key
            jwks = await self.get_jwks()
            key = None

            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                    break

            if not key:
                raise ClerkAuthError(f"Unable to find key with kid: {kid}")

            # Verify and decode token
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self.issuer,
                options={"verify_aud": False}  # Clerk doesn't use aud claim
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise ClerkAuthError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ClerkAuthError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise ClerkAuthError(f"Token verification failed: {str(e)}")


clerk_auth = ClerkAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user from Clerk JWT token
    """
    try:
        token = credentials.credentials
        payload = await clerk_auth.verify_token(token)

        # Extract user information from payload
        user_data = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "username": payload.get("username"),
            "first_name": payload.get("given_name"),
            "last_name": payload.get("family_name"),
            "image_url": payload.get("picture"),
            "created_at": payload.get("iat"),
            "updated_at": payload.get("updated_at"),
        }

        if not user_data["id"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token"
            )

        return user_data

    except ClerkAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user but make it optional (for public endpoints)
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
