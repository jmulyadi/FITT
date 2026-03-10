from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from dependencies import get_backend
from schemas import WorkoutCreate, WorkoutUpdate, ExerciseCreate, ExerciseUpdate, SetCreate, SetUpdate
from DBhelpermethods import FitnessBackend

router = APIRouter()


# ============================================================================
# WORKOUTS
# ============================================================================

@router.post("/", status_code=status.HTTP_201_CREATED)
def add_workout(body: WorkoutCreate, backend: FitnessBackend = Depends(get_backend)):
    """
    Logs a new workout. type must be 'cardio' or 'strength'.
    If cardio, cardio_type and distance are also required.
    """
    username = backend.get_username_from_session()
    try:
        workout_id = backend.add_workout(
            username=username,
            date=body.date,
            duration=body.duration,
            calories_burned=body.calories_burned,
            workout_type=body.type,
            cardio_type=body.cardio_type,
            distance=body.distance
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"workout_id": workout_id}


@router.get("/")
def get_workouts(
    start_date: Optional[str] = Query(default=None, description="Filter from this date YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="Filter to this date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """
    Returns workouts for the current user, most recent first.
    Optionally filter by date range using start_date and/or end_date query params.
    - No params: all workouts
    - start_date only: all workouts on or after that date
    - end_date only: all workouts on or before that date
    - both: workouts between the two dates (inclusive)
    """
    username = backend.get_username_from_session()
    if start_date and end_date:
        return backend.get_workouts_in_range(username, start_date, end_date)
    if start_date:
        return backend.get_workouts_in_range(username, start_date, "2100-01-01")
    if end_date:
        return backend.get_workouts_in_range(username, "2000-01-01", end_date)
    return backend.get_all_workouts(username)



# ============================================================================
# EXERCISE SEARCH  (must be before /{workout_id} to avoid route conflict)
# ============================================================================

@router.get("/exercise-search")
def search_exercises(
    name: str = Query(description="Exercise name or partial name, e.g. 'bench', 'curl'"),
    limit: int = Query(default=10, ge=1, le=50),
    backend: FitnessBackend = Depends(get_backend)
):
    """
    Search ExerciseDB for exercises by name.
    Proxies to the ExerciseDB external API.
    """
    from ExerciseDBAPImethods import ExerciseDBClient
    try:
        client = ExerciseDBClient()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"ExerciseDB unavailable: {e}")
    try:
        results = client.search_by_name(name, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ExerciseDB error: {e}")
    return {"count": len(results), "exercises": results}


@router.get("/{workout_id}")
def get_workout(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single workout with all nested exercises and sets."""
    try:
        return backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{workout_id}")
def update_workout(
    workout_id: int,
    body: WorkoutUpdate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates fields on a workout."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")
    try:
        return backend.update_workout(workout_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Deletes a workout and all its exercises and sets."""
    try:
        backend.delete_workout(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# ANALYTICS  — scoped to a specific workout
# ============================================================================

@router.get("/{workout_id}/analytics/summary")
def get_workout_summary(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """
    Summary for a specific workout: calories burned, duration, type,
    number of exercises and sets (strength) or distance (cardio).
    """
    try:
        workout = backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    exercises = workout.get("exercise", [])
    total_sets = sum(len(ex.get("SET", [])) for ex in exercises)
    total_volume = sum(
        s.get("weight", 0) * s.get("reps", 0)
        for ex in exercises
        for s in ex.get("SET", [])
    )

    summary = {
        "workout_id": workout_id,
        "date": workout.get("date"),
        "type": workout.get("type"),
        "duration_minutes": workout.get("duration"),
        "calories_burned": workout.get("calories_burned"),
    }

    if workout.get("type") == "cardio":
        summary["cardio_type"] = workout.get("cardio_type")
        summary["distance_km"] = workout.get("distance")
    else:
        summary["total_exercises"] = len(exercises)
        summary["total_sets"] = total_sets
        summary["total_volume_kg"] = total_volume

    return summary


@router.get("/{workout_id}/analytics/net-calories")
def get_net_calories(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """
    Net calories for the date of this workout.
    Compares all calories burned that day vs all calories consumed that day.
    """
    try:
        workout = backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    username = backend.get_username_from_session()
    return backend.get_net_calories(username, workout.get("date"))


@router.get("/{workout_id}/analytics/progress/{exercise_name}")
def get_exercise_progress(
    workout_id: int,
    exercise_name: str,
    backend: FitnessBackend = Depends(get_backend)
):
    """
    Tracks progress for a specific exercise across all workouts up to and including
    this workout's date. Returns max weight and total volume per session.
    """
    try:
        workout = backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    username = backend.get_username_from_session()
    return backend.get_exercise_progress(username, exercise_name, "2000-01-01", workout.get("date"))


# ============================================================================
# EXERCISES
# ============================================================================

@router.post("/{workout_id}/exercises", status_code=status.HTTP_201_CREATED)
def add_exercise(workout_id: int, body: ExerciseCreate, backend: FitnessBackend = Depends(get_backend)):
    """Adds an exercise to a strength workout."""
    try:
        exercise_id = backend.add_exercise(workout_id, body.name, body.muscle_group)
        return {"exercise_id": exercise_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{workout_id}/exercises")
def get_exercises(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns all exercises for a workout with their sets."""
    return backend.get_exercises_by_workout(workout_id)


@router.get("/{workout_id}/exercises/{exercise_id}")
def get_exercise(workout_id: int, exercise_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single exercise with all its sets."""
    try:
        return backend.get_exercise_by_id(exercise_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{workout_id}/exercises/{exercise_id}")
def update_exercise(
    workout_id: int,
    exercise_id: int,
    body: ExerciseUpdate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates name or muscle_group of an exercise."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")
    try:
        return backend.update_exercise(exercise_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{workout_id}/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(workout_id: int, exercise_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Deletes an exercise and all its sets."""
    try:
        backend.delete_exercise(exercise_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# SETS
# ============================================================================

@router.post("/{workout_id}/exercises/{exercise_id}/sets", status_code=status.HTTP_201_CREATED)
def add_set(workout_id: int, exercise_id: int, body: SetCreate, backend: FitnessBackend = Depends(get_backend)):
    """Adds a set to an exercise."""
    try:
        return backend.add_set(exercise_id, body.set_num, body.reps, body.weight, body.intensity)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{workout_id}/exercises/{exercise_id}/sets")
def get_sets(workout_id: int, exercise_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns all sets for an exercise, ordered by set number."""
    return backend.get_sets_by_exercise(exercise_id)


@router.get("/{workout_id}/exercises/{exercise_id}/sets/{set_id}")
def get_set(workout_id: int, exercise_id: int, set_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single set."""
    try:
        return backend.get_set_by_id(set_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{workout_id}/exercises/{exercise_id}/sets/{set_id}")
def update_set(
    workout_id: int,
    exercise_id: int,
    set_id: int,
    body: SetUpdate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates reps, weight, intensity, or set_num."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")
    try:
        return backend.update_set(set_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{workout_id}/exercises/{exercise_id}/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(workout_id: int, exercise_id: int, set_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Deletes a set."""
    try:
        backend.delete_set(set_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))