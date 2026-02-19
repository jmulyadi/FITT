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
bearer_scheme = HTTPBearer(auto_error=False)


def get_authenticated_client(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Client:
    """
    Validates the Bearer JWT from the Authorization header.
    Returns a Supabase client with the user's session active.
    Raises 401 if the token is missing, invalid, or expired.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    try:
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Pass empty string as refresh_token — this client is scoped to one request
        # and will never need to refresh; using the access token as refresh token is wrong.
        client.auth.set_session(token, "")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return client


def get_backend(
    client: Client = Depends(get_authenticated_client),
) -> FitnessBackend:
    """
    Returns an authenticated FitnessBackend for the current request.
    Passes the already-resolved user_id so FitnessBackend never needs
    to call auth.get_user() a second time per request.
    """
    # The client session is already validated; pull user_id from it once here
    # so get_username_from_session() only needs a single DB lookup, not two.
    user_response = client.auth.get_user()
    user_id = user_response.user.id
    return FitnessBackend(client, user_id)


def get_admin_client() -> Client:
    """Returns a Supabase admin client for privileged operations (e.g. delete account)."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)