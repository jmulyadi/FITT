from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client
from dotenv import load_dotenv
from schemas import (
    SignUpRequest, SignInRequest, RefreshRequest,
    ResetPasswordRequest, UpdatePasswordRequest
)
from dependencies import get_authenticated_client, get_admin_client
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

router = APIRouter()


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def sign_up(body: SignUpRequest):
    """Register a new user. Returns user_id, username, and email."""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    auth_response = client.auth.sign_up({
        "email": body.email,
        "password": body.password
    })

    if not auth_response.user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sign up failed.")

    user_id = auth_response.user.id

    profile_data = {
        "id": user_id,
        "username": body.username,
        "age": body.age,
        "gender": body.gender,
        "weight": body.weight,
        "height": body.height,
        "experience_level": body.experience_level,
        "bmi": body.bmi,
    }

    try:
        response = client.table("USER").insert(profile_data).execute()
        if not response.data:
            raise RuntimeError("Profile insert returned no data.")
    except Exception as e:
        admin_client.auth.admin.delete_user(user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sign up failed during profile creation: {e}"
        )

    return {"user_id": user_id, "username": body.username, "email": body.email}


@router.post("/signin")
def sign_in(body: SignInRequest):
    """
    Sign in and receive access_token + refresh_token.
    Pass the access_token as a Bearer token on all protected routes.
    """
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    try:
        auth_response = client.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not auth_response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    client.auth.set_session(
        auth_response.session.access_token,
        auth_response.session.refresh_token
    )

    profile = client.table("USER") \
        .select("username") \
        .eq("id", auth_response.user.id) \
        .execute()

    username = profile.data[0]["username"] if profile.data else None

    return {
        "user_id": auth_response.user.id,
        "username": username,
        "access_token": auth_response.session.access_token,
        "refresh_token": auth_response.session.refresh_token,
        "expires_at": auth_response.session.expires_at,
    }


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
def sign_out(client=Depends(get_authenticated_client)):
    """Invalidates the current session."""
    client.auth.sign_out()


@router.post("/refresh")
def refresh_session(body: RefreshRequest):
    """Exchange a refresh_token for a new access_token."""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    try:
        response = client.auth.refresh_session(body.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session refresh failed. Please sign in again."
        )

    if not response.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session refresh failed. Please sign in again."
        )

    return {
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
        "expires_at": response.session.expires_at,
    }


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password_request(body: ResetPasswordRequest):
    """Sends a password reset email to the given address."""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.auth.reset_password_email(body.email)


@router.patch("/update-password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(body: UpdatePasswordRequest, client=Depends(get_authenticated_client)):
    """Updates the password for the currently authenticated user."""
    client.auth.update_user({"password": body.new_password})


@router.delete("/delete-account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(client=Depends(get_authenticated_client)):
    """
    Permanently deletes the authenticated user's account and all their data.
    CASCADE handles wiping workouts, meals, and all child records.
    """
    user_response = client.auth.get_user()
    if not user_response or not user_response.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    user_id = user_response.user.id
    admin_client = get_admin_client()
    admin_client.auth.admin.delete_user(user_id)