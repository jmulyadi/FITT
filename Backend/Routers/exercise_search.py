from readline import backend

from fastapi import APIRouter, Depends, HTTPException, status, Query
from dependencies import get_backend
from DBhelpermethods import FitnessBackend
from ExerciseDBAPImethods import ExerciseDBClient
from pydantic import BaseModel

router = APIRouter()


def get_exercise_client() -> ExerciseDBClient:
    try:
        return ExerciseDBClient()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ExerciseDB client could not be initialised: {e}"
        )


# ============================================================================
# SEARCH / BROWSE  (read-only, no DB write)
# ============================================================================

@router.get("/search")
def search_exercises_by_name(
    name: str = Query(description="Exercise name or partial name, e.g. 'bench', 'curl'"),
    limit: int = Query(default=10, ge=1, le=50),
    client: ExerciseDBClient = Depends(get_exercise_client)
):
    """
    Search ExerciseDB by exercise name.
    Returns a list of matching exercises with instructions, muscles, and GIF URLs.
    """
    try:
        results = client.search_by_name(name, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ExerciseDB error: {e}")

    return {"count": len(results), "exercises": results}


@router.get("/body-part/{body_part}")
def get_exercises_by_body_part(
    body_part: str,
    limit: int = Query(default=10, ge=1, le=50),
    client: ExerciseDBClient = Depends(get_exercise_client)
):
    """
    Browse exercises by body part (e.g. chest, back, shoulders, upper legs).
    Call GET /exercise-search/body-parts for the full list.
    """
    try:
        results = client.get_exercises_by_body_part(body_part, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ExerciseDB error: {e}")

    return {"count": len(results), "exercises": results}


@router.get("/target/{muscle}")
def get_exercises_by_target_muscle(
    muscle: str,
    limit: int = Query(default=10, ge=1, le=50),
    client: ExerciseDBClient = Depends(get_exercise_client)
):
    """
    Browse exercises by target muscle (e.g. pectorals, quads, biceps).
    Call GET /exercise-search/muscles for the full list.
    """
    try:
        results = client.get_exercises_by_target(muscle, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ExerciseDB error: {e}")

    return {"count": len(results), "exercises": results}


@router.get("/equipment/{equipment}")
def get_exercises_by_equipment(
    equipment: str,
    limit: int = Query(default=10, ge=1, le=50),
    client: ExerciseDBClient = Depends(get_exercise_client)
):
    """
    Browse exercises by equipment type.
    Call GET /exercise-search/equipment for the full list.
    """
    try:
        results = client.get_exercises_by_equipment(equipment, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ExerciseDB error: {e}")

    return {"count": len(results), "exercises": results}


@router.get("/body-parts")
def get_body_part_list(client: ExerciseDBClient = Depends(get_exercise_client)):
    """Returns the full list of valid body part values for filtering."""
    try:
        return client.get_body_part_list()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ExerciseDB error: {e}")


@router.get("/muscles")
def get_target_muscle_list(client: ExerciseDBClient = Depends(get_exercise_client)):
    """Returns the full list of valid target muscle values for filtering."""
    try:
        return client.get_target_list()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ExerciseDB error: {e}")


@router.get("/equipment")
def get_equipment_list(client: ExerciseDBClient = Depends(get_exercise_client)):
    """Returns the full list of valid equipment values for filtering."""
    try:
        return client.get_equipment_list()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"ExerciseDB error: {e}")


# ============================================================================
# SAVE TO WORKOUT  (DB write)
# ============================================================================

class SaveExerciseRequest(BaseModel):
    exercise_db_id: str  # ExerciseDB's own ID string e.g. "0001"


@router.post("/save/{workout_id}", status_code=status.HTTP_201_CREATED)
def save_exercise_to_workout(
    workout_id: int,
    body: SaveExerciseRequest,
    backend: FitnessBackend = Depends(get_backend),
    client: ExerciseDBClient = Depends(get_exercise_client)
):
    """
    Looks up an exercise from ExerciseDB by its ID, then saves it directly
    to the specified workout in one call.
    """
    # Fetch full exercise details from ExerciseDB
    try:
        ex = client.get_exercise_by_id(body.exercise_db_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not fetch exercise from ExerciseDB: {e}"
        )

    if not ex or not ex.get("name"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No exercise found in ExerciseDB with id '{body.exercise_db_id}'."
        )

    name = ex.get("name", "Unknown").title()
    # Use target muscle as muscle group, fall back to bodyPart
    muscle_group = (ex.get("target") or ex.get("bodyPart") or "Unknown").title()

    try:
        username = backend.get_username_from_session()
        backend.verify_workout_ownership(username, workout_id)
        exercise_id = backend.add_exercise(workout_id, name, muscle_group)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not save exercise to workout: {e}"
        )

    return {
        "exercise_id": exercise_id,
        "name": name,
        "muscle_group": muscle_group,
        "body_part": ex.get("bodyPart", "").title(),
        "equipment": ex.get("equipment", "").title(),
        "gif_url": ex.get("gifUrl"),
        "instructions": ex.get("instructions", []),
    }