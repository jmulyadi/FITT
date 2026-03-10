import os

from DBhelpermethods import FitnessBackend
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

bearer_scheme = HTTPBearer()


def get_authenticated_client(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Client:
    """
    Validates the Bearer JWT issued by Supabase Auth on the frontend.
    Raises 401 if the token is missing, invalid, or expired.
    """
    token = credentials.credentials
    client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    try:
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
            )
        client.auth.postgrest.auth(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    return client


def get_backend(
    client: Client = Depends(get_authenticated_client),
) -> FitnessBackend:
    """Returns an authenticated FitnessBackend for the current request."""
    return FitnessBackend(client)


def get_admin_client() -> Client:
    """Returns a Supabase admin client for privileged operations."""
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

