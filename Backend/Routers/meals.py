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
def add_meal(user_id: str, body: MealCreate, backend: FitnessBackend = Depends(get_backend)):
    meal_id = backend.add_meal(body.date, body.meal_num, body.calories_in)
    return {"meal_id": meal_id}


@router.get("/date/{date_string}")
def get_meals_by_date(user_id: str, date_string: str, backend: FitnessBackend = Depends(get_backend)):
    return backend.get_daily_meals(date_string)


@router.get("/")
def get_meals(user_id: str, 
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    backend: FitnessBackend = Depends(get_backend)
):
    if start_date and end_date:
        return backend.get_meals_in_range(start_date, end_date)
    if start_date:
        return backend.get_meals_in_range(start_date, "2100-01-01")
    if end_date:
        return backend.get_meals_in_range("2000-01-01", end_date)
    return backend.get_meals_in_range("2000-01-01", "2100-01-01")


@router.get("/analytics/summary")
def get_global_nutrition_summary(user_id: str, 
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    return backend.get_nutrition_summary(start_date, end_date)


@router.get("/analytics/calories-consumed")
def get_total_calories_consumed(user_id: str, 
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    total = backend.get_total_calories_consumed(start_date, end_date)
    return {"total_calories_consumed": total, "start_date": start_date, "end_date": end_date}


@router.get("/{meal_id}")
def get_meal(user_id: str, meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        return backend.get_meal_by_id(meal_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{meal_id}")
def update_meal(user_id: str, meal_id: int, body: MealUpdate, backend: FitnessBackend = Depends(get_backend)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided.")
    try:
        return backend.update_meal(meal_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(user_id: str, meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        backend.delete_meal(meal_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# MEAL ANALYTICS
# ============================================================================

@router.get("/{meal_id}/analytics/summary")
def get_meal_summary(user_id: str, meal_id: int, backend: FitnessBackend = Depends(get_backend)):
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
        "calories_by_type": type_breakdown,
    }


# ============================================================================
# FOOD
# ============================================================================

@router.post("/{meal_id}/food", status_code=status.HTTP_201_CREATED)
def add_food(user_id: str, meal_id: int, body: FoodCreate, backend: FitnessBackend = Depends(get_backend)):
    try:
        return backend.add_food_to_meal(meal_id, body.name, body.food_type, body.calories)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{meal_id}/food")
def get_food_by_meal(user_id: str, meal_id: int, backend: FitnessBackend = Depends(get_backend)):
    return backend.get_foods_by_meal(meal_id)


@router.get("/{meal_id}/food/{food_id}")
def get_food(user_id: str, meal_id: int, food_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        return backend.get_food_by_id(food_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{meal_id}/food/{food_id}")
def update_food(user_id: str, meal_id: int, food_id: int, body: FoodUpdate, backend: FitnessBackend = Depends(get_backend)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided.")
    try:
        return backend.update_food(food_id, **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{meal_id}/food/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(user_id: str, meal_id: int, food_id: int, backend: FitnessBackend = Depends(get_backend)):
    try:
        backend.delete_food_item(food_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# FOOD SEARCH (USDA API)
# ============================================================================

from USDAAPImethods import USDAFoodDataClient as _USDAClient

def _usda_client():
    return _USDAClient()

def _format_product(product: dict) -> dict:
    """Maps USDA FoodData Central response to the FITT application schema."""
    
    # Helper to extract specific nutrient values from the USDA list structure
    def get_nutrient(name_id: str):
        nutrients = product.get("foodNutrients", [])
        for n in nutrients:
            # Check for name (used in search) or nutrientName (used in details)
            n_name = n.get("nutrientName", n.get("name", "")).lower()
            if name_id.lower() in n_name:
                return n.get("value") or n.get("amount")
        return None

    # Construct serving size string
    serving_val = product.get("servingSize")
    serving_unit = product.get("servingSizeUnit", "")
    serving_str = f"{serving_val} {serving_unit}".strip() if serving_val else None

    return {
        "barcode": product.get("gtinUpc") or str(product.get("fdcId")),
        "name": product.get("description", "Unknown").title(),
        "brand": product.get("brandOwner") or product.get("brandName") or "N/A",
        "serving_size": serving_str,
        "nutriscore": None,  # USDA does not provide Nutri-Score grades
        "calories_per_100g": get_nutrient("Energy"),
        "calories_per_serving": None, 
        "protein_g": get_nutrient("Protein"),
        "carbs_g": get_nutrient("Carbohydrate"),
        "fat_g": get_nutrient("Total lipid (fat)"),
        "image_url": None, # USDA API does not consistently provide product images
    }


@router.get("/food-search/search")
def search_food(user_id: str, 
    query: str = Query(description="Food name, e.g. 'chicken breast'"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=50),
):
    try:
        # result now comes from the fixed USDAFoodDataClient
        result = _usda_client().search_products(
            query=query, page_number=page, page_size=page_size
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"USDA API error: {e}")
    
    # Process products safely
    raw_foods = result.get("foods", [])
    products = [_format_product(p) for p in raw_foods]
    
    return {
        "count": result.get("totalHits", len(products)), 
        "page": page, 
        "products": products
    }


@router.get("/food-search/barcode/{barcode}")
def get_food_by_barcode(user_id: str, barcode: str):
    try:
        # USDA barcode lookups are executed as a filtered search
        result = _usda_client().get_product_by_barcode(barcode)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"USDA API error: {e}")
        
    if result.get("status") != 1:
        raise HTTPException(status_code=404, detail=f"No product found with barcode '{barcode}'.")
        
    return _format_product(result.get("product", {}))