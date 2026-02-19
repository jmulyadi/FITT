from fastapi import APIRouter, Depends, HTTPException, status
from dependencies import get_backend
from schemas import SetCreate, SetUpdate
from DBhelpermethods import FitnessBackend

router = APIRouter()


@router.post("/{exercise_id}", status_code=status.HTTP_201_CREATED)
def add_set(
    exercise_id: int,
    body: SetCreate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Adds a set to an exercise."""
    try:
        username = backend.get_username_from_session()
        backend.verify_exercise_ownership(username, exercise_id)
        return backend.add_set(exercise_id, body.set_num, body.reps, body.weight, body.intensity)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/exercise/{exercise_id}")
def get_sets_by_exercise(exercise_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns all sets for a given exercise, ordered by set number."""
    return backend.get_sets_by_exercise(exercise_id)


@router.get("/{set_id}")
def get_set(set_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single set by ID."""
    try:
        return backend.get_set_by_id(set_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{set_id}")
def update_set(
    set_id: int,
    body: SetUpdate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates reps, weight, intensity, or set_num for a set."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update."
        )
    try:
        username = backend.get_username_from_session()
        backend.verify_set_ownership(username, set_id)
        return backend.update_set(set_id, **updates)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(set_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Deletes a single set."""
    try:
        username = backend.get_username_from_session()
        backend.verify_set_ownership(username, set_id)
        backend.delete_set(set_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))