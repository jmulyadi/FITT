from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from dependencies import get_backend
from DBhelpermethods import FitnessBackend
from OpenFoodFactsAPImethods import OpenFoodFactsClient
from pydantic import BaseModel, Field

router = APIRouter()


def get_food_client() -> OpenFoodFactsClient:
    return OpenFoodFactsClient()


def _extract_calories(nutriments: dict, serving_size_g: Optional[float]) -> int:
    """
    Best-effort calorie extraction from OpenFoodFacts nutriments dict.
    Prefers per-serving value if a serving size is known, otherwise uses per-100g.
    Returns 0 if no calorie data is available.
    """
    # Per-serving calories (most accurate if serving size is on the label)
    serving_kcal = nutriments.get("energy-kcal_serving")
    if serving_kcal is not None:
        return round(serving_kcal)

    # Fall back to per-100g and scale by serving size if provided
    per_100g = nutriments.get("energy-kcal_100g")
    if per_100g is not None and serving_size_g:
        return round(per_100g * serving_size_g / 100)

    # Last resort: just use per-100g as-is
    if per_100g is not None:
        return round(per_100g)

    return 0


def _parse_serving_size(serving_str: Optional[str]) -> Optional[float]:
    """Tries to extract a gram value from a serving size string like '30g' or '1 cup (240ml)'."""
    if not serving_str:
        return None
    import re
    match = re.search(r"(\d+(?:\.\d+)?)\s*g", serving_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _format_product(product: dict) -> dict:
    """Extracts the fields your frontend and DB care about from a raw OFF product."""
    nutriments = product.get("nutriments", {})
    serving_str = product.get("serving_size")
    serving_g = _parse_serving_size(serving_str)

    return {
        "barcode": product.get("code") or product.get("_id"),
        "name": product.get("product_name") or product.get("abbreviated_product_name") or "Unknown",
        "brand": product.get("brands"),
        "serving_size": serving_str,
        "nutriscore": product.get("nutrition_grades", "").upper() or None,
        "nova_group": product.get("nova_group"),
        "calories_per_100g": nutriments.get("energy-kcal_100g") or 0,
        "calories_per_serving": nutriments.get("energy-kcal_serving") or (
            round(nutriments["energy-kcal_100g"] * serving_g / 100)
            if nutriments.get("energy-kcal_100g") and serving_g else 0
        ),
        "protein_g": nutriments.get("proteins_100g"),
        "carbs_g": nutriments.get("carbohydrates_100g"),
        "fat_g": nutriments.get("fat_100g"),
        "fiber_g": nutriments.get("fiber_100g"),
        "sugar_g": nutriments.get("sugars_100g"),
        "image_url": product.get("image_front_url"),
    }


# ============================================================================
# SEARCH / LOOKUP  (read-only, no DB write)
# ============================================================================

@router.get("/search")
def search_food(
    query: str = Query(description="Food name to search, e.g. 'chicken breast', 'oats'"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    client: OpenFoodFactsClient = Depends(get_food_client)
):
    """
    Search OpenFoodFacts by food name.
    Returns a list of matching products with calorie and macro info.
    """
    try:
        result = client.search_products(
            query=query,
            page=page,
            page_size=page_size,
            fields=[
                "code", "_id", "product_name", "abbreviated_product_name",
                "brands", "serving_size", "nutrition_grades", "nova_group",
                "nutriments", "image_front_url"
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenFoodFacts error: {e}")

    products = result.get("products", [])
    formatted = [_format_product(p) for p in products]

    return {
        "count": result.get("count", len(formatted)),
        "page": page,
        "page_size": page_size,
        "products": formatted,
    }


@router.get("/barcode/{barcode}")
def get_food_by_barcode(
    barcode: str,
    client: OpenFoodFactsClient = Depends(get_food_client)
):
    """
    Look up a product by its barcode (e.g. from a phone scanner).
    Returns calorie and macro info.
    """
    try:
        result = client.get_product_by_barcode(
            barcode,
            fields=[
                "code", "_id", "product_name", "brands", "serving_size",
                "nutrition_grades", "nova_group", "nutriments", "image_front_url"
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenFoodFacts error: {e}")

    if result.get("status") != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No product found with barcode '{barcode}'."
        )

    return _format_product(result.get("product", {}))


# ============================================================================
# SAVE TO MEAL  (DB write)
# ============================================================================

class SaveFoodByBarcodeRequest(BaseModel):
    barcode: str
    food_type: str = Field(
        default="Other",
        description="Category label e.g. Protein, Carbs, Snack, Drink"
    )
    servings: float = Field(
        default=1.0,
        gt=0,
        le=50,
        description="Number of servings eaten. Calories are multiplied by this."
    )


class SaveFoodBySearchRequest(BaseModel):
    name: str = Field(description="Exact product name from search results")
    calories: int = Field(ge=0, le=10000, description="Calories to log (copy from search result)")
    food_type: str = Field(
        default="Other",
        description="Category label e.g. Protein, Carbs, Snack, Drink"
    )


@router.post("/save-by-barcode/{meal_id}", status_code=status.HTTP_201_CREATED)
def save_food_by_barcode(
    meal_id: int,
    body: SaveFoodByBarcodeRequest,
    backend: FitnessBackend = Depends(get_backend),
    client: OpenFoodFactsClient = Depends(get_food_client)
):
    """
    Looks up a product by barcode from OpenFoodFacts, then logs it to the
    specified meal in one call. Calories are auto-calculated from nutrition data.
    """
    try:
        result = client.get_product_by_barcode(
            body.barcode,
            fields=[
                "code", "product_name", "brands", "serving_size",
                "nutrition_grades", "nutriments"
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenFoodFacts error: {e}")

    if result.get("status") != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No product found with barcode '{body.barcode}'."
        )

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not save food to meal: {e}"
        )

    return {
        **saved,
        "servings": body.servings,
        "calories_per_serving": calories_per_serving,
        "nutriscore": product.get("nutrition_grades", "").upper() or None,
    }


@router.post("/save-by-name/{meal_id}", status_code=status.HTTP_201_CREATED)
def save_food_by_name(
    meal_id: int,
    body: SaveFoodBySearchRequest,
    backend: FitnessBackend = Depends(get_backend),
):
    """
    Saves a food item to a meal using data the user already has from a search result.
    Use this after GET /food-search/search â€” the user picks a result, you pass
    the name and calories directly.
    """
    try:
        username = backend.get_username_from_session()
        backend.verify_meal_ownership(username, meal_id)
        saved = backend.add_food_to_meal(meal_id, body.name, body.food_type, body.calories)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not save food to meal: {e}"
        )

    return saved