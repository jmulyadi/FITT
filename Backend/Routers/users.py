from fastapi import APIRouter, Depends, HTTPException, status
from dependencies import get_backend
from schemas import UpdateProfileRequest
from DBhelpermethods import FitnessBackend

router = APIRouter()


@router.get("/me")
def get_my_profile(backend: FitnessBackend = Depends(get_backend)):
    """Returns the profile of the currently authenticated user."""
    username = backend.get_username_from_session()
    return backend.get_user(username)


@router.patch("/me")
def update_my_profile(
    body: UpdateProfileRequest,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates allowed profile fields. Only pass fields you want to change."""
    username = backend.get_username_from_session()
    updates = body.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update."
        )

    return backend.update_user_profile(username, **updates)