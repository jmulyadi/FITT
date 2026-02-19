from fastapi import APIRouter, Depends, HTTPException, status
from dependencies import get_backend
from schemas import ExerciseCreate, ExerciseUpdate
from DBhelpermethods import FitnessBackend

router = APIRouter()


@router.post("/{workout_id}", status_code=status.HTTP_201_CREATED)
def add_exercise(
    workout_id: int,
    body: ExerciseCreate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Adds an exercise to a strength workout. Returns the new exercise_id."""
    try:
        username = backend.get_username_from_session()
        backend.verify_workout_ownership(username, workout_id)
        exercise_id = backend.add_exercise(workout_id, body.name, body.muscle_group)
        return {"exercise_id": exercise_id}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/workout/{workout_id}")
def get_exercises_by_workout(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns all exercises for a strength workout, including their sets."""
    return backend.get_exercises_by_workout(workout_id)


@router.get("/{exercise_id}")
def get_exercise(exercise_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single exercise with all its sets."""
    try:
        return backend.get_exercise_by_id(exercise_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{exercise_id}")
def update_exercise(
    exercise_id: int,
    body: ExerciseUpdate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates the name or muscle_group of an exercise."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update."
        )
    try:
        username = backend.get_username_from_session()
        backend.verify_exercise_ownership(username, exercise_id)
        return backend.update_exercise(exercise_id, **updates)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Deletes an exercise and all its sets."""
    try:
        username = backend.get_username_from_session()
        backend.verify_exercise_ownership(username, exercise_id)
        backend.delete_exercise(exercise_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))