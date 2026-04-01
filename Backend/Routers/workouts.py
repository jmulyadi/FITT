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
def add_workout(user_id: str, body: WorkoutCreate, backend: FitnessBackend = Depends(get_backend)):
    try:
        workout_id = backend.add_workout(
            date=body.date,
            duration=body.duration,
            calories_burned=body.calories_burned,
            workout_type=body.type,
            cardio_type=body.cardio_type,
            distance=body.distance,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"workout_id": workout_id}


@router.get("/")
def get_workouts(user_id: str, 
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    backend: FitnessBackend = Depends(get_backend)
):
    if start_date and end_date:
        return backend.get_workouts_in_range(start_date, end_date)
    if start_date:
        return backend.get_workouts_in_range(start_date, "2100-01-01")
    if end_date:
        return backend.get_workouts_in_range("2000-01-01", end_date)
    return backend.get_all_workouts()


@router.get("/exercise-search")
def search_exercises(user_id: str, 
    name: str = Query(description="Exercise name or partial name"),
    limit: int = Query(default=10, ge=1, le=50),
    backend: FitnessBackend = Depends(get_backend)
):
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


@router.get("/analytics/summary")
def get_global_workout_summary(user_id: str, 
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    return backend.get_workout_summary(start_date, end_date)


@router.get("/analytics/calories-burned")
def get_total_calories_burned(user_id: str, 
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    total = backend.get_total_calories_burned(start_date, end_date)
    return {"total_calories_burned": total, "start_date": start_date, "end_date": end_date}


@router.get("/analytics/average-duration")
def get_average_duration(user_id: str, 
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    avg = backend.get_average_workout_duration(start_date, end_date)
    return {"average_duration_minutes": avg, "start_date": start_date, "end_date": end_date}


@router.get("/analytics/progress/{exercise_name}")
def get_global_exercise_progress(user_id: str, 
    exercise_name: str,
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    return backend.get_exercise_progress(exercise_name, start_date, end_date)


@router.get("/analytics/net-calories/{date_string}")
def get_net_calories_by_date(user_id: str, date_string: str, backend: FitnessBackend = Depends(get_backend)):
    return backend.get_net_calories(date_string)


@router.get("/{workout_id}")
def get_workout(user_id: str, workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        return backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{workout_id}")
def update_workout(user_id: str, workout_id: int, body: WorkoutUpdate, backend: FitnessBackend = Depends(get_backend)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided.")
    try:
        return backend.update_workout(workout_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(user_id: str, workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        backend.delete_workout(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# ANALYTICS — scoped to a specific workout
# ============================================================================

@router.get("/{workout_id}/analytics/summary")
def get_workout_summary(user_id: str, workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        workout = backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    exercises = workout.get("exercise", [])
    total_sets = sum(len(ex.get("SET", [])) for ex in exercises)
    total_volume = sum(s.get("weight", 0) * s.get("reps", 0) for ex in exercises for s in ex.get("SET", []))
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
def get_net_calories(user_id: str, workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        workout = backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return backend.get_net_calories(workout.get("date"))


@router.get("/{workout_id}/analytics/progress/{exercise_name}")
def get_exercise_progress(user_id: str, workout_id: int, exercise_name: str, backend: FitnessBackend = Depends(get_backend)):
    try:
        workout = backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return backend.get_exercise_progress(exercise_name, "2000-01-01", workout.get("date"))


# ============================================================================
# EXERCISES
# ============================================================================

@router.post("/{workout_id}/exercises", status_code=status.HTTP_201_CREATED)
def add_exercise(user_id: str, workout_id: int, body: ExerciseCreate, backend: FitnessBackend = Depends(get_backend)):
    try:
        exercise_id = backend.add_exercise(workout_id, body.name, body.muscle_group)
        return {"exercise_id": exercise_id}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{workout_id}/exercises")
def get_exercises(user_id: str, workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    return backend.get_exercises_by_workout(workout_id)


@router.get("/{workout_id}/exercises/{exercise_id}")
def get_exercise(user_id: str, workout_id: int, exercise_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        return backend.get_exercise_by_id(exercise_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{workout_id}/exercises/{exercise_id}")
def update_exercise(user_id: str, workout_id: int, exercise_id: int, body: ExerciseUpdate, backend: FitnessBackend = Depends(get_backend)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided.")
    try:
        return backend.update_exercise(exercise_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{workout_id}/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(user_id: str, workout_id: int, exercise_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        backend.delete_exercise(exercise_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# SETS
# ============================================================================

@router.post("/{workout_id}/exercises/{exercise_id}/sets", status_code=status.HTTP_201_CREATED)
def add_set(user_id: str, workout_id: int, exercise_id: int, body: SetCreate, backend: FitnessBackend = Depends(get_backend)):
    try:
        return backend.add_set(exercise_id, body.set_num, body.reps, body.weight, body.intensity)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{workout_id}/exercises/{exercise_id}/sets")
def get_sets(user_id: str, workout_id: int, exercise_id: int, backend: FitnessBackend = Depends(get_backend)):
    return backend.get_sets_by_exercise(exercise_id)


@router.get("/{workout_id}/exercises/{exercise_id}/sets/{set_id}")
def get_set(user_id: str, workout_id: int, exercise_id: int, set_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        return backend.get_set_by_id(set_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{workout_id}/exercises/{exercise_id}/sets/{set_id}")
def update_set(user_id: str, workout_id: int, exercise_id: int, set_id: int, body: SetUpdate, backend: FitnessBackend = Depends(get_backend)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided.")
    try:
        return backend.update_set(set_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{workout_id}/exercises/{exercise_id}/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(user_id: str, workout_id: int, exercise_id: int, set_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        backend.delete_set(set_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))