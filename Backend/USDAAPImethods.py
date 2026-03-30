import requests
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables once at the module level
load_dotenv()

class USDAFoodDataClient:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the USDA FoodData Central API client.
        """
        # Prioritize passed key, then environment variable
        self.api_key = api_key or os.getenv('USDA_API_KEY')
        
        if not self.api_key:
            # This helps debug if the .env is not being read
            print("CRITICAL: USDA_API_KEY not found in environment or .env file.")
            
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.headers = {"Accept": "application/json"}
        self._TIMEOUT = 30

    def _get(self, endpoint: str, params: dict = None) -> Dict[str, Any]:
        """Internal helper for GET requests with API key injection."""
        url = f"{self.base_url}/{endpoint}"
        query_params = params or {}
        query_params["api_key"] = self.api_key
        
        try:
            response = requests.get(
                url, headers=self.headers, params=query_params, timeout=self._TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # This is what triggers the 502 in meals.py
            raise RuntimeError(f"USDA API error: {e}")

    def _post(self, endpoint: str, json_data: dict) -> Dict[str, Any]:
        """Internal helper for POST requests."""
        url = f"{self.base_url}/{endpoint}"
        # USDA accepts api_key as a query parameter even on POST requests
        params = {"api_key": self.api_key}
        
        try:
            response = requests.post(
                url, headers=self.headers, params=params, json=json_data, timeout=self._TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"USDA API error: {e}")

    # -------------------------------------------------------------------------
    # READ OPERATIONS
    # -------------------------------------------------------------------------

    def get_product_by_barcode(self, barcode: str) -> Dict[str, Any]:
        """
        USDA finds barcodes via the search endpoint. 
        Returns the first 'Branded' match found.
        """
        search_data = {
            "query": barcode,
            "dataType": ["Branded"],
            "pageSize": 1
        }
        result = self._post("foods/search", search_data)
        
        # Format to match your previous 'status' logic
        foods = result.get("foods", [])
        if foods:
            return {"status": 1, "product": foods[0], "status_verbose": "product found"}
        return {"status": 0, "status_verbose": "product not found"}

    def get_food_by_id(self, fdc_id: str) -> Dict[str, Any]:
        """Retrieve full details for a specific food item using its FDC ID."""
        return self._get(f"food/{fdc_id}")

    def search_products(self, query: str, page_size: int = 10, page_number: int = 1) -> Dict[str, Any]:
        """
        Full-text search for food items.
        """
        search_data = {
            "query": query,
            "pageSize": page_size,
            "pageNumber": page_number,
            "dataType": ["Branded", "Foundation", "Survey (FNDDS)"]
        }
        return self._post("foods/search", search_data)

    # -------------------------------------------------------------------------
    # UTILITY METHODS
    # -------------------------------------------------------------------------

    def extract_nutrients(self, food_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps the USDA's list-based nutrient structure to a flat dictionary
        similar to the Open Food Facts format for your Supabase/PostgreSQL JSON storage.
        """
        nutrients = food_item.get("foodNutrients", [])
        # USDA uses different keys depending on the endpoint (search vs details)
        # We check for 'nutrientName' (search) and 'nutrient'->'name' (details)
        flat_map = {}
        
        mapping = {
            "Energy": "energy-kcal_100g",
            "Protein": "proteins_100g",
            "Total lipid (fat)": "fat_100g",
            "Carbohydrate, by difference": "carbohydrates_100g",
            "Fiber, total dietary": "fiber_100g",
            "Sugars, total including added": "sugars_100g",
            "Sodium, Na": "sodium_100g"
        }

        for n in nutrients:
            name = n.get("nutrientName") or n.get("nutrient", {}).get("name")
            value = n.get("value") or n.get("amount")
            
            if name in mapping:
                flat_map[mapping[name]] = value
        
        return flat_map

# -------------------------------------------------------------------------
# Formatting Helpers
# -------------------------------------------------------------------------

def print_product(result: Dict[str, Any]) -> None:
    if result.get("status") != 1:
        print("Product not found.")
        return

    food = result.get("product", {})
    client = USDAFoodDataClient(api_key=os.getenv("USDA_API_KEY"))
    nutriments = client.extract_nutrients(food)

    print("\n" + "=" * 80)
    print(f"  {food.get('description', 'Unknown Food').title()}")
    print("=" * 80)
    print(f"  Brand:          {food.get('brandOwner', food.get('brandName', 'N/A'))}")
    print(f"  FDC ID:         {food.get('fdcId', 'N/A')}")
    print(f"  Serving Size:   {food.get('servingSize', 'N/A')} {food.get('servingSizeUnit', '')}")
    
    if nutriments:
        print("\n  Nutrition Summary:")
        for key, val in nutriments.items():
            print(f"    {key:<22} {val}")
    print("=" * 80 + "\n")