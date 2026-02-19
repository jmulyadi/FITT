from fastapi import APIRouter, Depends, HTTPException, status
from dependencies import get_backend
from schemas import CardioCreate, CardioUpdate
from DBhelpermethods import FitnessBackend

router = APIRouter()


@router.post("/{workout_id}", status_code=status.HTTP_201_CREATED)
def add_cardio(
    workout_id: int,
    body: CardioCreate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Adds cardio details to an existing workout."""
    try:
        username = backend.get_username_from_session()
        backend.verify_workout_ownership(username, workout_id)
        return backend.add_cardio(workout_id, body.cardio_type, body.distance)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/workout/{workout_id}")
def get_cardio_by_workout(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns the cardio details for a specific workout."""
    try:
        return backend.get_cardio_by_workout(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/date/{date_string}")
def get_cardio_by_date(date_string: str, backend: FitnessBackend = Depends(get_backend)):
    """Returns all cardio workouts on a specific date (YYYY-MM-DD)."""
    username = backend.get_username_from_session()
    return backend.get_cardio_workouts_by_date(username, date_string)


@router.patch("/{workout_id}")
def update_cardio(
    workout_id: int,
    body: CardioUpdate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates cardio_type or distance for a workout's cardio record."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update."
        )
    try:
        username = backend.get_username_from_session()
        backend.verify_workout_ownership(username, workout_id)
        return backend.update_cardio(workout_id, **updates)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cardio(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Removes cardio data from a workout."""
    try:
        username = backend.get_username_from_session()
        backend.verify_workout_ownership(username, workout_id)
        backend.delete_cardio(workout_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))