from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from DBhelpermethods import FitnessBackend
import os

bearer_scheme = HTTPBearer()


def get_authenticated_client(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> tuple[Client, str]:
    """
    Validates the Bearer token and returns (client, user_id).
    The client has the token applied to both auth session and postgrest.
    """
    token = credentials.credentials
    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")

    client: Client = create_client(url, anon_key)

    try:
        user_response = client.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
            )

        user_id = user_response.user.id

        # Set auth session so RLS policies see auth.uid() correctly
        client.auth.set_session(token, token)
        # Also apply directly to postgrest as belt-and-suspenders
        client.postgrest.auth(token)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    return client, user_id


def get_backend(
    auth: tuple = Depends(get_authenticated_client),
) -> FitnessBackend:
    client, user_id = auth
    return FitnessBackend(client, user_id)


def get_admin_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, service_key)