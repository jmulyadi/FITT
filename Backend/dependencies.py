from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from dotenv import load_dotenv
from DBhelpermethods import FitnessBackend
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

bearer_scheme = HTTPBearer()


def get_authenticated_client(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Client:
    """
    Validates the Bearer JWT from the Authorization header.
    Returns a Supabase client with the user's session active.
    Raises 401 if the token is missing, invalid, or expired.
    """
    token = credentials.credentials

    client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    try:
        # Verify the token is valid and get user info
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
            )
        # Set the session so all subsequent DB calls respect RLS
        client.auth.set_session(token, "")
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
    """Returns a Supabase admin client for privileged operations (e.g. delete account)."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)