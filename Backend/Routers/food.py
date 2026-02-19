from fastapi import APIRouter, Depends, HTTPException, status
from dependencies import get_backend
from schemas import FoodCreate, FoodUpdate
from DBhelpermethods import FitnessBackend

router = APIRouter()


@router.post("/{meal_id}", status_code=status.HTTP_201_CREATED)
def add_food(
    meal_id: int,
    body: FoodCreate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Adds a food item to an existing meal."""
    try:
        username = backend.get_username_from_session()
        backend.verify_meal_ownership(username, meal_id)
        return backend.add_food_to_meal(meal_id, body.name, body.food_type, body.calories)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/meal/{meal_id}")
def get_foods_by_meal(meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns all food items for a specific meal."""
    return backend.get_foods_by_meal(meal_id)


@router.get("/{food_id}")
def get_food(food_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single food item by ID."""
    try:
        return backend.get_food_by_id(food_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{food_id}")
def update_food(
    food_id: int,
    body: FoodUpdate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates name, food_type, or calories for a food item."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update."
        )
    try:
        username = backend.get_username_from_session()
        backend.verify_food_ownership(username, food_id)
        return backend.update_food(food_id, **updates)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(food_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Removes a food item from a meal."""
    try:
        username = backend.get_username_from_session()
        backend.verify_food_ownership(username, food_id)
        backend.delete_food_item(food_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))