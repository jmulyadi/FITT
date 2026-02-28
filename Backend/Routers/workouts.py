from fastapi import APIRouter, Depends, HTTPException, status, Query
from dependencies import get_backend
from schemas import WorkoutCreate, WorkoutUpdate, ExerciseCreate, ExerciseUpdate, SetCreate, SetUpdate
from DBhelpermethods import FitnessBackend

router = APIRouter()


# ============================================================================
# WORKOUTS  /users/{user_id}/workouts
# ============================================================================

@router.post("/{user_id}/workouts", status_code=status.HTTP_201_CREATED)
def add_workout(
    user_id: str,
    body: WorkoutCreate,
    backend: FitnessBackend = Depends(get_backend)
):
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


@router.get("/{user_id}/workouts")
def get_all_workouts(user_id: str, backend: FitnessBackend = Depends(get_backend)):
    """Returns all workouts for the user, most recent first."""
    username = backend.get_username_from_session()
    return backend.get_all_workouts(username)


@router.get("/{user_id}/workouts/date/{date_string}")
def get_workouts_by_date(
    user_id: str,
    date_string: str,
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns all workouts on a specific date with nested exercises and sets."""
    username = backend.get_username_from_session()
    return backend.get_workouts_by_date(username, date_string)


@router.get("/{user_id}/workouts/range")
def get_workouts_in_range(
    user_id: str,
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns all workouts between two dates (inclusive)."""
    username = backend.get_username_from_session()
    return backend.get_workouts_in_range(username, start_date, end_date)


@router.get("/{user_id}/workouts/{workout_id}")
def get_workout(
    user_id: str,
    workout_id: int,
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns a single workout with all nested exercises and sets."""
    try:
        return backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{user_id}/workouts/{workout_id}")
def update_workout(
    user_id: str,
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


@router.delete("/{user_id}/workouts/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    user_id: str,
    workout_id: int,
    backend: FitnessBackend = Depends(get_backend)
):
    """Deletes a workout and all its exercises and sets."""
    try:
        backend.delete_workout(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# EXERCISES  /users/{user_id}/workouts/{workout_id}/exercises
# ============================================================================

@router.post("/{user_id}/workouts/{workout_id}/exercises", status_code=status.HTTP_201_CREATED)
def add_exercise(
    user_id: str,
    workout_id: int,
    body: ExerciseCreate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Adds an exercise to a strength workout."""
    try:
        exercise_id = backend.add_exercise(workout_id, body.name, body.muscle_group)
        return {"exercise_id": exercise_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}/workouts/{workout_id}/exercises")
def get_exercises(
    user_id: str,
    workout_id: int,
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns all exercises for a workout with their sets."""
    return backend.get_exercises_by_workout(workout_id)


@router.get("/{user_id}/workouts/{workout_id}/exercises/{exercise_id}")
def get_exercise(
    user_id: str,
    workout_id: int,
    exercise_id: int,
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns a single exercise with all its sets."""
    try:
        return backend.get_exercise_by_id(exercise_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{user_id}/workouts/{workout_id}/exercises/{exercise_id}")
def update_exercise(
    user_id: str,
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


@router.delete("/{user_id}/workouts/{workout_id}/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    user_id: str,
    workout_id: int,
    exercise_id: int,
    backend: FitnessBackend = Depends(get_backend)
):
    """Deletes an exercise and all its sets."""
    try:
        backend.delete_exercise(exercise_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# SETS  /users/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/sets
# ============================================================================

@router.post("/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/sets", status_code=status.HTTP_201_CREATED)
def add_set(
    user_id: str,
    workout_id: int,
    exercise_id: int,
    body: SetCreate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Adds a set to an exercise."""
    try:
        return backend.add_set(exercise_id, body.set_num, body.reps, body.weight, body.intensity)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/sets")
def get_sets(
    user_id: str,
    workout_id: int,
    exercise_id: int,
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns all sets for an exercise, ordered by set number."""
    return backend.get_sets_by_exercise(exercise_id)


@router.get("/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/sets/{set_id}")
def get_set(
    user_id: str,
    workout_id: int,
    exercise_id: int,
    set_id: int,
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns a single set."""
    try:
        return backend.get_set_by_id(set_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/sets/{set_id}")
def update_set(
    user_id: str,
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


@router.delete("/{user_id}/workouts/{workout_id}/exercises/{exercise_id}/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(
    user_id: str,
    workout_id: int,
    exercise_id: int,
    set_id: int,
    backend: FitnessBackend = Depends(get_backend)
):
    """Deletes a set."""
    try:
        backend.delete_set(set_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# WORKOUT ANALYTICS  /users/{user_id}/workouts/analytics/...
# ============================================================================

@router.get("/{user_id}/workouts/analytics/summary")
def get_workout_summary(
    user_id: str,
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Workout summary: total workouts, calories, duration, cardio/strength counts."""
    username = backend.get_username_from_session()
    return backend.get_workout_summary(username, start_date, end_date)


@router.get("/{user_id}/workouts/analytics/calories-burned")
def get_calories_burned(
    user_id: str,
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Total calories burned across workouts in a date range."""
    username = backend.get_username_from_session()
    total = backend.get_total_calories_burned(username, start_date, end_date)
    return {"total_calories_burned": total, "start_date": start_date, "end_date": end_date}


@router.get("/{user_id}/workouts/analytics/average-duration")
def get_average_duration(
    user_id: str,
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Average workout duration in minutes across a date range."""
    username = backend.get_username_from_session()
    avg = backend.get_average_workout_duration(username, start_date, end_date)
    return {"average_duration_minutes": avg, "start_date": start_date, "end_date": end_date}


@router.get("/{user_id}/workouts/analytics/progress/{exercise_name}")
def get_exercise_progress(
    user_id: str,
    exercise_name: str,
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Tracks max weight and total volume for a specific exercise over time."""
    username = backend.get_username_from_session()
    return backend.get_exercise_progress(username, exercise_name, start_date, end_date)


@router.get("/{user_id}/workouts/analytics/net-calories/{date_string}")
def get_net_calories(
    user_id: str,
    date_string: str,
    backend: FitnessBackend = Depends(get_backend)
):
    """Calories consumed vs burned for a specific date."""
    username = backend.get_username_from_session()
    return backend.get_net_calories(username, date_string)