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


@router.get("/")
def get_all_meals(
    start_date: Optional[str] = Query(default=None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns meals for the user. Optionally filter by date range."""
    username = backend.get_username_from_session()
    if start_date and end_date:
        return backend.get_meals_in_range(username, start_date, end_date)
    return backend.get_meals_in_range(username, "2000-01-01", "2100-01-01")


@router.get("/date/{date_string}")
def get_meals_by_date(date_string: str, backend: FitnessBackend = Depends(get_backend)):
    """Returns all meals and food items for a specific date."""
    username = backend.get_username_from_session()
    return backend.get_daily_meals(username, date_string)


@router.get("/analytics/summary")
def get_nutrition_summary(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Nutrition summary: total meals, total calories, averages per day and per meal."""
    username = backend.get_username_from_session()
    return backend.get_nutrition_summary(username, start_date, end_date)


@router.get("/analytics/calories-consumed")
def get_calories_consumed(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Total calories consumed across all meals in a date range."""
    username = backend.get_username_from_session()
    total = backend.get_total_calories_consumed(username, start_date, end_date)
    return {"total_calories_consumed": total, "start_date": start_date, "end_date": end_date}


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
# FOOD SEARCH (OpenFoodFacts bridge)
# ============================================================================

from OpenFoodFactsAPImethods import OpenFoodFactsClient
from pydantic import BaseModel as _BaseModel, Field as _Field
import re as _re


def _get_food_client() -> OpenFoodFactsClient:
    return OpenFoodFactsClient()


def _parse_serving_size(serving_str):
    if not serving_str:
        return None
    match = _re.search(r"(\d+(?:\.\d+)?)\s*g", serving_str, _re.IGNORECASE)
    return float(match.group(1)) if match else None


def _extract_calories(nutriments, serving_size_g):
    serving_kcal = nutriments.get("energy-kcal_serving")
    if serving_kcal is not None:
        return round(serving_kcal)
    per_100g = nutriments.get("energy-kcal_100g")
    if per_100g is not None and serving_size_g:
        return round(per_100g * serving_size_g / 100)
    if per_100g is not None:
        return round(per_100g)
    return 0


def _format_product(product):
    nutriments = product.get("nutriments", {})
    serving_str = product.get("serving_size")
    serving_g = _parse_serving_size(serving_str)
    return {
        "barcode": product.get("code") or product.get("_id"),
        "name": product.get("product_name") or product.get("abbreviated_product_name") or "Unknown",
        "brand": product.get("brands"),
        "serving_size": serving_str,
        "nutriscore": product.get("nutrition_grades", "").upper() or None,
        "calories_per_100g": nutriments.get("energy-kcal_100g"),
        "calories_per_serving": nutriments.get("energy-kcal_serving") or (
            round(nutriments["energy-kcal_100g"] * serving_g / 100)
            if nutriments.get("energy-kcal_100g") and serving_g else None
        ),
        "protein_g": nutriments.get("proteins_100g"),
        "carbs_g": nutriments.get("carbohydrates_100g"),
        "fat_g": nutriments.get("fat_100g"),
        "fiber_g": nutriments.get("fiber_100g"),
        "sugar_g": nutriments.get("sugars_100g"),
        "image_url": product.get("image_front_url"),
    }


@router.get("/food-search")
def search_food(
    query: str = Query(description="Food name, e.g. 'chicken breast', 'oats'"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    client: OpenFoodFactsClient = Depends(_get_food_client)
):
    """Search OpenFoodFacts by food name. Returns products with calorie and macro info."""
    try:
        result = client.search_products(
            query=query, page=page, page_size=page_size,
            fields=["code", "_id", "product_name", "abbreviated_product_name",
                    "brands", "serving_size", "nutrition_grades",
                    "nutriments", "image_front_url"]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    products = result.get("products", [])
    return {"count": result.get("count", len(products)), "page": page,
            "page_size": page_size, "products": [_format_product(p) for p in products]}


@router.get("/food-search/barcode/{barcode}")
def get_food_by_barcode(
    barcode: str,
    client: OpenFoodFactsClient = Depends(_get_food_client)
):
    """Look up a product by barcode (e.g. from a phone scanner)."""
    try:
        result = client.get_product_by_barcode(
            barcode,
            fields=["code", "_id", "product_name", "brands", "serving_size",
                    "nutrition_grades", "nutriments", "image_front_url"]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    if result.get("status") != 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No product found with barcode '{barcode}'.")
    return _format_product(result.get("product", {}))


class _SaveByBarcodeRequest(_BaseModel):
    barcode: str
    food_type: str = _Field(default="Other", description="e.g. Protein, Carbs, Snack, Drink")
    servings: float = _Field(default=1.0, gt=0, le=50,
                             description="Number of servings. Calories are multiplied by this.")


class _SaveByNameRequest(_BaseModel):
    name: str
    calories: int = _Field(ge=0, le=10000)
    food_type: str = _Field(default="Other")


@router.post("/{meal_id}/food-search/save-by-barcode", status_code=status.HTTP_201_CREATED)
def save_food_by_barcode(
    meal_id: int,
    body: _SaveByBarcodeRequest,
    backend: FitnessBackend = Depends(get_backend),
    client: OpenFoodFactsClient = Depends(_get_food_client)
):
    """
    Scan a barcode → calories auto-calculated → food logged to meal in one call.
    Typical flow: scan barcode → call this → food saved.
    Pass servings (default 1.0) to multiply calories accordingly.
    """
    try:
        result = client.get_product_by_barcode(
            body.barcode,
            fields=["code", "product_name", "brands", "serving_size", "nutrition_grades", "nutriments"]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if result.get("status") != 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No product found with barcode '{body.barcode}'.")

    product = result.get("product", {})
    nutriments = product.get("nutriments", {})
    serving_g = _parse_serving_size(product.get("serving_size"))
    calories_per_serving = _extract_calories(nutriments, serving_g)
    total_calories = round(calories_per_serving * body.servings)
    name = product.get("product_name") or "Unknown Product"
    brand = product.get("brands")
    display_name = f"{name} ({brand})" if brand else name

    try:
        saved = backend.add_food_to_meal(meal_id, display_name, body.food_type, total_calories)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {**saved, "servings": body.servings, "calories_per_serving": calories_per_serving,
            "nutriscore": product.get("nutrition_grades", "").upper() or None}


@router.post("/{meal_id}/food-search/save-by-name", status_code=status.HTTP_201_CREATED)
def save_food_by_name(
    meal_id: int,
    body: _SaveByNameRequest,
    backend: FitnessBackend = Depends(get_backend)
):
    """
    After searching, user picks a result — pass name + calories to log it.
    Typical flow: search food → pick result → call this → food saved.
    """
    try:
        return backend.add_food_to_meal(meal_id, body.name, body.food_type, body.calories)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))