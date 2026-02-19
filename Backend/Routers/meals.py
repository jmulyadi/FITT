from fastapi import APIRouter, Depends, HTTPException, status, Query
from dependencies import get_backend
from schemas import MealCreate, MealUpdate
from DBhelpermethods import FitnessBackend

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_meal(body: MealCreate, backend: FitnessBackend = Depends(get_backend)):
    """Logs a meal. Returns the new meal_id."""
    username = backend.get_username_from_session()
    meal_id = backend.add_meal(username, body.date, body.meal_num, body.calories_in)
    return {"meal_id": meal_id}


@router.get("/date/{date_string}")
def get_daily_meals(date_string: str, backend: FitnessBackend = Depends(get_backend)):
    """Returns all meals and their food items for a specific date, ordered by meal number."""
    username = backend.get_username_from_session()
    return backend.get_daily_meals(username, date_string)


@router.get("/range")
def get_meals_in_range(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns all meals between two dates (inclusive) with food items."""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be less than or equal to end_date."
        )
    username = backend.get_username_from_session()
    return backend.get_meals_in_range(username, start_date, end_date)


@router.get("/{meal_id}")
def get_meal(meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single meal with all its food items."""
    try:
        return backend.get_meal_by_id(meal_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{meal_id}")
def update_meal(
    meal_id: int,
    body: MealUpdate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates meal_num or calories_in for a meal."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update."
        )
    try:
        username = backend.get_username_from_session()
        backend.verify_meal_ownership(username, meal_id)
        return backend.update_meal(meal_id, **updates)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Deletes a meal and all its food items."""
    try:
        username = backend.get_username_from_session()
        backend.verify_meal_ownership(username, meal_id)
        backend.delete_meal(meal_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))