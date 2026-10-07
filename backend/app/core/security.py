import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional

# Setup Supabase JWT secret from env var (e.g. from Render environment)
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "dummy_secret_for_local_dev")
ALGORITHM = "HS256"

security = HTTPBearer()

class TokenData(BaseModel):
    sub: str
    email: Optional[str] = None
    role: Optional[str] = None

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Validates Supabase JWT.
    Enforces Phase 07 Security constraints:
    - Verifies signature using SUPABASE_JWT_SECRET.
    - Verifies audience.
    - Ensures user is authenticated (not anon).
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            SUPABASE_JWT_SECRET, 
            algorithms=[ALGORITHM], 
            audience="authenticated"
        )
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        token_data = TokenData(sub=sub, email=payload.get("email"), role=payload.get("role"))
        
        # Enforce that token is from a signed-in user, not anon role
        if token_data.role != "authenticated":
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions: Must be authenticated",
            )
            
        return token_data
    except JWTError:
        raise credentials_exception

def get_current_user_subject(token_data: TokenData = Depends(verify_token)) -> str:
    """Returns the unique subject ID from the identity provider."""
    return token_data.sub
