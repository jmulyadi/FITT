from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from dependencies import get_backend
from schemas import MealCreate, MealUpdate, FoodCreate, FoodUpdate
from DBhelpermethods import FitnessBackend

router = APIRouter()


# ============================================================================
# MEALS
# ============================================================================

@router.post("/", status_code=status.HTTP_201_CREATED)
def add_meal(body: MealCreate, backend: FitnessBackend = Depends(get_backend)):
    """Logs a meal. Returns the new meal_id."""
    username = backend.get_username_from_session()
    meal_id = backend.add_meal(username, body.date, body.meal_num, body.calories_in)
    return {"meal_id": meal_id}


@router.get("/date/{date_string}")
def get_meals_by_date(date_string: str, backend: FitnessBackend = Depends(get_backend)):
    """Returns all meals and food items for a specific date (YYYY-MM-DD)."""
    username = backend.get_username_from_session()
    return backend.get_daily_meals(username, date_string)


@router.get("/")
def get_meals(
    start_date: Optional[str] = Query(default=None, description="Filter from this date YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="Filter to this date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """
    Returns meals for the current user with all food items nested.
    Optionally filter by date range using start_date and/or end_date query params.
    - No params: all meals
    - start_date only: all meals on or after that date
    - end_date only: all meals on or before that date
    - both: meals between the two dates (inclusive)
    """
    username = backend.get_username_from_session()
    if start_date and end_date:
        return backend.get_meals_in_range(username, start_date, end_date)
    if start_date:
        return backend.get_meals_in_range(username, start_date, "2100-01-01")
    if end_date:
        return backend.get_meals_in_range(username, "2000-01-01", end_date)
    return backend.get_meals_in_range(username, "2000-01-01", "2100-01-01")



@router.get("/{meal_id}")
def get_meal(meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single meal with all its food items."""
    try:
        return backend.get_meal_by_id(meal_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{meal_id}")
def update_meal(meal_id: int, body: MealUpdate, backend: FitnessBackend = Depends(get_backend)):
    """Updates meal_num or calories_in."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")
    try:
        return backend.update_meal(meal_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Deletes a meal and all its food items."""
    try:
        backend.delete_meal(meal_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# ANALYTICS — scoped to a specific meal
# ============================================================================

@router.get("/{meal_id}/analytics/summary")
def get_meal_summary(meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    """
    Summary for a specific meal: total calories, number of food items,
    and a breakdown by food type.
    """
    try:
        meal = backend.get_meal_by_id(meal_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    foods = meal.get("food", [])
    type_breakdown = {}
    for food in foods:
        food_type = food.get("type", "Other")
        type_breakdown[food_type] = type_breakdown.get(food_type, 0) + food.get("calories", 0)

    return {
        "meal_id": meal_id,
        "date": meal.get("date"),
        "meal_num": meal.get("meal_num"),
        "total_calories": meal.get("calories_in"),
        "total_food_items": len(foods),
        "calories_by_type": type_breakdown
    }


# ============================================================================
# FOOD
# ============================================================================

@router.post("/{meal_id}/food", status_code=status.HTTP_201_CREATED)
def add_food(meal_id: int, body: FoodCreate, backend: FitnessBackend = Depends(get_backend)):
    """Adds a food item to a meal."""
    try:
        return backend.add_food_to_meal(meal_id, body.name, body.food_type, body.calories)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{meal_id}/food")
def get_food_by_meal(meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns all food items for a meal."""
    return backend.get_foods_by_meal(meal_id)


@router.get("/{meal_id}/food/{food_id}")
def get_food(meal_id: int, food_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single food item."""
    try:
        return backend.get_food_by_id(food_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{meal_id}/food/{food_id}")
def update_food(meal_id: int, food_id: int, body: FoodUpdate, backend: FitnessBackend = Depends(get_backend)):
    """Updates name, food_type, or calories for a food item."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")
    try:
        return backend.update_food(food_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{meal_id}/food/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(meal_id: int, food_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Removes a food item from a meal."""
    try:
        backend.delete_food_item(food_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# ============================================================================
# FOOD SEARCH (OpenFoodFacts) — no auth needed, read-only external API
# ============================================================================

import re as _re
from OpenFoodFactsAPImethods import OpenFoodFactsClient as _OFFClient

def _off_client():
    return _OFFClient()

def _format_product(product: dict) -> dict:
    nutriments = product.get("nutriments", {})
    serving_str = product.get("serving_size")
    serving_g = None
    if serving_str:
        m = _re.search(r"(\d+(?:\.\d+)?)\s*g", serving_str, _re.IGNORECASE)
        if m:
            serving_g = float(m.group(1))
    per_100g = nutriments.get("energy-kcal_100g")
    cal_serving = nutriments.get("energy-kcal_serving")
    if not cal_serving and per_100g and serving_g:
        cal_serving = round(per_100g * serving_g / 100)
    return {
        "barcode": product.get("code") or product.get("_id"),
        "name": product.get("product_name_en") or product.get("product_name") or "Unknown",
        "brand": product.get("brands"),
        "serving_size": serving_str,
        "nutriscore": (product.get("nutrition_grades") or "").upper() or None,
        "calories_per_100g": per_100g,
        "calories_per_serving": cal_serving,
        "protein_g": nutriments.get("proteins_100g"),
        "carbs_g": nutriments.get("carbohydrates_100g"),
        "fat_g": nutriments.get("fat_100g"),
        "image_url": product.get("image_front_url"),
    }


@router.get("/food-search/search")
def search_food(
    query: str = Query(description="Food name, e.g. 'chicken breast'"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=50),
):
    """Search OpenFoodFacts by food name."""
    try:
        result = _off_client().search_products(
            query=query, page=page, page_size=page_size,
            fields=["code","_id","product_name","abbreviated_product_name",
                    "brands","serving_size","nutrition_grades","nutriments","image_front_url"]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"OpenFoodFacts error: {e}")
    products = [_format_product(p) for p in result.get("products", [])]
    return {"count": result.get("count", len(products)), "page": page, "products": products}


@router.get("/food-search/barcode/{barcode}")
def get_food_by_barcode(barcode: str):
    """Look up a product by barcode."""
    try:
        result = _off_client().get_product_by_barcode(barcode, fields=[
            "code","product_name","brands","serving_size",
            "nutrition_grades","nutriments","image_front_url"
        ])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenFoodFacts error: {e}")
    if result.get("status") != 1:
        raise HTTPException(status_code=404, detail=f"No product found with barcode '{barcode}'.")
    return _format_product(result.get("product", {}))