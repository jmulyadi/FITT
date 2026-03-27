from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client
from dotenv import load_dotenv
from dependencies import get_backend, get_authenticated_client
from schemas import SignUpRequest, UpdateProfileRequest
from DBhelpermethods import FitnessBackend
import os
import traceback

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(body: SignUpRequest):
    """
    Register a new user. Creates Supabase auth account and profile row.
    Returns user_id, username, and email.
    """
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
        print(f"Profile insert failed for user_id={user_id}: {e}")
        traceback.print_exc()

        rollback_error = None
        try:
            admin_client.auth.admin.delete_user(user_id)
        except Exception as delete_error:
            rollback_error = delete_error
            print(f"Rollback delete failed for user_id={user_id}: {delete_error}")
            traceback.print_exc()

        detail = f"Sign up failed during profile creation: {e}"
        if rollback_error:
            detail += f" | rollback failed: {rollback_error}"

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

    return {"user_id": user_id, "username": body.username, "email": body.email}


@router.get("/{user_id}")
def get_user(user_id: str, backend: FitnessBackend = Depends(get_backend)):
    """Returns the profile for the given Supabase auth UUID."""
    try:
        return backend.get_user_by_id(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{user_id}")
def update_user(
    user_id: str,
    body: UpdateProfileRequest,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates allowed profile fields for the given Supabase auth UUID."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update."
        )
    try:
        # Look up username from UUID, then update by username
        profile = backend.get_user_by_id(user_id)
        username = profile["username"]
        return backend.update_user_profile(username, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, client=Depends(get_authenticated_client)):
    """
    Permanently deletes the user's account and all their data.
    CASCADE handles wiping workouts, meals, and all child records.
    """
    admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    try:
        admin_client.auth.admin.delete_user(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete user: {e}"
        )
