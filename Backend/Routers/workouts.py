from fastapi import APIRouter, Depends, HTTPException, status, Query
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
def get_all_workouts(backend: FitnessBackend = Depends(get_backend)):
    """Returns all workouts for the current user, most recent first."""
    username = backend.get_username_from_session()
    return backend.get_all_workouts(username)


@router.get("/date/{date_string}")
def get_workouts_by_date(date_string: str, backend: FitnessBackend = Depends(get_backend)):
    """Returns all workouts on a specific date with nested exercises and sets."""
    username = backend.get_username_from_session()
    return backend.get_workouts_by_date(username, date_string)


@router.get("/range")
def get_workouts_in_range(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns all workouts between two dates (inclusive)."""
    username = backend.get_username_from_session()
    return backend.get_workouts_in_range(username, start_date, end_date)


@router.get("/analytics/summary")
def get_workout_summary(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Workout summary: total workouts, calories, duration, cardio/strength counts."""
    username = backend.get_username_from_session()
    return backend.get_workout_summary(username, start_date, end_date)


@router.get("/analytics/calories-burned")
def get_calories_burned(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Total calories burned across workouts in a date range."""
    username = backend.get_username_from_session()
    total = backend.get_total_calories_burned(username, start_date, end_date)
    return {"total_calories_burned": total, "start_date": start_date, "end_date": end_date}


@router.get("/analytics/average-duration")
def get_average_duration(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Average workout duration in minutes across a date range."""
    username = backend.get_username_from_session()
    avg = backend.get_average_workout_duration(username, start_date, end_date)
    return {"average_duration_minutes": avg, "start_date": start_date, "end_date": end_date}


@router.get("/analytics/net-calories/{date_string}")
def get_net_calories(date_string: str, backend: FitnessBackend = Depends(get_backend)):
    """Calories consumed vs burned for a specific date."""
    username = backend.get_username_from_session()
    return backend.get_net_calories(username, date_string)


@router.get("/analytics/progress/{exercise_name}")
def get_exercise_progress(
    exercise_name: str,
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Tracks max weight and total volume for a specific exercise over time."""
    username = backend.get_username_from_session()
    return backend.get_exercise_progress(username, exercise_name, start_date, end_date)


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

# ============================================================================
# EXERCISE SEARCH (ExerciseDB bridge)
# ============================================================================

from ExerciseDBAPImethods import ExerciseDBClient
from pydantic import BaseModel as _BaseModel


def _get_exercise_client() -> ExerciseDBClient:
    try:
        return ExerciseDBClient()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


class SaveExerciseRequest(_BaseModel):
    exercise_db_id: str


@router.get("/exercise-search")
def search_exercises(
    name: str = Query(description="Exercise name or partial name, e.g. 'bench', 'curl'"),
    limit: int = Query(default=10, ge=1, le=50),
    client: ExerciseDBClient = Depends(_get_exercise_client)
):
    """
    Search ExerciseDB by name.
    Returns exercises with instructions, target muscles, and GIF URLs.
    """
    try:
        results = client.search_by_name(name, limit=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return {"count": len(results), "exercises": results}


@router.get("/exercise-search/body-part/{body_part}")
def search_by_body_part(
    body_part: str,
    limit: int = Query(default=10, ge=1, le=50),
    client: ExerciseDBClient = Depends(_get_exercise_client)
):
    """Browse exercises by body part (e.g. chest, back, shoulders, upper legs)."""
    try:
        results = client.get_exercises_by_body_part(body_part, limit=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return {"count": len(results), "exercises": results}


@router.get("/exercise-search/muscle/{muscle}")
def search_by_muscle(
    muscle: str,
    limit: int = Query(default=10, ge=1, le=50),
    client: ExerciseDBClient = Depends(_get_exercise_client)
):
    """Browse exercises by target muscle (e.g. pectorals, quads, biceps)."""
    try:
        results = client.get_exercises_by_target(muscle, limit=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return {"count": len(results), "exercises": results}


@router.get("/exercise-search/equipment/{equipment}")
def search_by_equipment(
    equipment: str,
    limit: int = Query(default=10, ge=1, le=50),
    client: ExerciseDBClient = Depends(_get_exercise_client)
):
    """Browse exercises by equipment type (e.g. barbell, dumbbell, cable)."""
    try:
        results = client.get_exercises_by_equipment(equipment, limit=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return {"count": len(results), "exercises": results}


@router.post("/{workout_id}/exercise-search/save", status_code=status.HTTP_201_CREATED)
def save_exercise_from_search(
    workout_id: int,
    body: SaveExerciseRequest,
    backend: FitnessBackend = Depends(get_backend),
    client: ExerciseDBClient = Depends(_get_exercise_client)
):
    """
    Fetch an exercise from ExerciseDB by its id and save it to a workout in one call.
    Typical flow:
      1. Search with GET /workouts/exercise-search?name=bench
      2. User picks a result — grab its id field
      3. POST here with that id and the target workout_id
    """
    try:
        ex = client.get_exercise_by_id(body.exercise_db_id)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if not ex or not ex.get("name"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No exercise found with id '{body.exercise_db_id}'.")

    name = ex.get("name", "Unknown").title()
    muscle_group = (ex.get("target") or ex.get("bodyPart") or "Unknown").title()

    try:
        exercise_id = backend.add_exercise(workout_id, name, muscle_group)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "exercise_id": exercise_id,
        "name": name,
        "muscle_group": muscle_group,
        "equipment": ex.get("equipment", "").title(),
        "gif_url": ex.get("gifUrl"),
        "instructions": ex.get("instructions", []),
    }