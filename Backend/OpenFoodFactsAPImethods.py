import requests
from typing import List, Dict, Any, Optional


class OpenFoodFactsClient:
    def __init__(self, app_name: str = "FITT", app_version: str = "1.0"):
        """
        Initialize the Open Food Facts API client.

        Args:
            app_name: Your application name (sent in User-Agent header as good practice)
            app_version: Your application version
        """
        self.base_url = "https://world.openfoodfacts.org"
        self.api_v2 = f"{self.base_url}/api/v2"

        # Set User-Agent as recommended by Open Food Facts
        self.user_agent = f"{app_name}/{app_version} (Python client)"
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json"
        }

    # -------------------------------------------------------------------------
    # READ OPERATIONS
    # -------------------------------------------------------------------------

    def get_product_by_barcode(
        self,
        barcode: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get a product by its barcode .

        Args:
            barcode: The product barcode (e.g., "3017624010701")
            fields: Optional list of specific fields to return, e.g.:
                    ["product_name", "nutrition_grades", "nutriments", "ingredients_text"]
                    Omit to return all available fields.

        Returns:
            Dictionary containing:
            - status: 1 if found, 0 if not found
            - status_verbose: Human-readable status (e.g., "product found")
            - product: Nested dictionary with all product data, including:
                - product_name: Product name
                - brands: Brand name(s)
                - categories: Product categories
                - ingredients_text: Raw ingredients text
                - ingredients: Parsed list of ingredient dictionaries
                - allergens: Allergen information
                - nutrition_grades: Nutri-Score letter (a–e)
                - nutriscore_data: Detailed Nutri-Score breakdown
                - nutriments: Dictionary of nutritional values per 100g/serving:
                    - energy-kcal_100g, fat_100g, saturated-fat_100g,
                      carbohydrates_100g, sugars_100g, fiber_100g,
                      proteins_100g, salt_100g, sodium_100g
                - serving_size: Serving size string
                - quantity: Product quantity/weight
                - packaging: Packaging type(s)
                - labels: Certification labels (e.g., "organic", "fair-trade")
                - countries: Countries where the product is sold
                - image_front_url: URL to front-of-pack image
                - image_nutrition_url: URL to nutrition label image
                - image_ingredients_url: URL to ingredients image
                - ecoscore_grade: Eco-Score environmental grade (a–e)
                - nova_group: NOVA food processing group (1–4)
                - additives_tags: List of detected food additives
        """
        url = f"{self.api_v2}/product/{barcode}"
        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def search_products(
        self,
        query: Optional[str] = None,
        categories_tags_en: Optional[str] = None,
        nutrition_grades_tags: Optional[str] = None,
        labels_tags_en: Optional[str] = None,
        brands_tags: Optional[str] = None,
        countries_tags_en: Optional[str] = None,
        nova_groups_tags: Optional[str] = None,
        fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 24,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for products using various filters.

        Args:
            query: Full-text search string (e.g., "chocolate").
            categories_tags_en: Filter by category (e.g., "Orange juices")
            nutrition_grades_tags: Filter by Nutri-Score grade ("a", "b", "c", "d", or "e")
            labels_tags_en: Filter by label (e.g., "organic", "fair-trade")
            brands_tags: Filter by brand slug (e.g., "nestle", "kelloggs")
            countries_tags_en: Filter by country (e.g., "United States")
            nova_groups_tags: Filter by NOVA group ("1", "2", "3", or "4")
            fields: List of fields to include in each product result
            page: Page number (default: 1)
            page_size: Results per page (default: 24, max: 1000)
            sort_by: Sort order. Options:
                     "unique_scans_n" (popularity), "product_name",
                     "created_t" (newest), "last_modified_t" (recently updated)

        Returns:
            Dictionary containing:
            - count: Total number of matching products
            - page: Current page number
            - page_count: Number of pages
            - page_size: Results per page
            - products: List of product dictionaries (fields depend on `fields` param)
        """
        if query:
            # Full-text search requires v1 endpoint
            url = f"{self.base_url}/cgi/search.pl"
            params: Dict[str, Any] = {
                "search_terms": query,
                "action": "process",
                "json": 1,
                "page": page,
                "page_size": page_size,
            }
        else:
            url = f"{self.api_v2}/search"
            params = {"page": page, "page_size": page_size}

        if categories_tags_en:
            params["categories_tags_en"] = categories_tags_en
        if nutrition_grades_tags:
            params["nutrition_grades_tags"] = nutrition_grades_tags
        if labels_tags_en:
            params["labels_tags_en"] = labels_tags_en
        if brands_tags:
            params["brands_tags"] = brands_tags
        if countries_tags_en:
            params["countries_tags_en"] = countries_tags_en
        if nova_groups_tags:
            params["nova_groups_tags"] = nova_groups_tags
        if fields:
            params["fields"] = ",".join(fields)
        if sort_by:
            params["sort_by"] = sort_by

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_products_by_category(
        self,
        category: str,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Get all products in a specific category.

        Args:
            category: Category slug (e.g., "cereals", "cheeses", "beverages").
                      Use lowercase with hyphens for multi-word categories
                      (e.g., "breakfast-cereals").
            page: Page number (default: 1; each page returns ~20 products)

        Returns:
            Dictionary containing:
            - count: Total number of products in the category
            - page: Current page number
            - page_count: Total number of pages
            - products: List of product dictionaries
        """
        url = f"{self.base_url}/category/{category}.json"
        params = {"page": page}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_products_by_label(self, label: str, page: int = 1) -> Dict[str, Any]:
        """
        Get products matching a specific label or certification.

        Args:
            label: Label slug (e.g., "organic", "fair-trade", "gluten-free",
                   "vegan", "vegetarian")
            page: Page number (default: 1)

        Returns:
            Dictionary containing count, page, page_count, and products list.
        """
        url = f"{self.base_url}/label/{label}.json"
        params = {"page": page}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_products_by_brand(self, brand: str, page: int = 1) -> Dict[str, Any]:
        """
        Get all products from a specific brand.

        Args:
            brand: Brand slug in lowercase with hyphens (e.g., "nestle",
                   "kelloggs", "coca-cola")
            page: Page number (default: 1)

        Returns:
            Dictionary containing count, page, page_count, and products list.
        """
        url = f"{self.base_url}/brand/{brand}.json"
        params = {"page": page}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_products_by_ingredient(self, ingredient: str, page: int = 1) -> Dict[str, Any]:
        """
        Get products containing a specific ingredient.

        Args:
            ingredient: Ingredient slug in lowercase with hyphens
                        (e.g., "sugar", "palm-oil", "high-fructose-corn-syrup")
            page: Page number (default: 1)

        Returns:
            Dictionary containing count, page, page_count, and products list.
        """
        url = f"{self.base_url}/ingredient/{ingredient}.json"
        params = {"page": page}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_products_by_allergen(self, allergen: str, page: int = 1) -> Dict[str, Any]:
        """
        Get products that contain a specific allergen.

        Args:
            allergen: Allergen slug (e.g., "gluten", "milk", "eggs", "nuts",
                      "peanuts", "soybeans", "celery", "mustard")
            page: Page number (default: 1)

        Returns:
            Dictionary containing count, page, page_count, and products list.
        """
        url = f"{self.base_url}/allergen/{allergen}.json"
        params = {"page": page}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_categories_list(self) -> Dict[str, Any]:
        """
        Get the full list of available product categories.

        Returns:
            Dictionary containing:
            - count: Total number of categories
            - tags: List of category tag dictionaries, each with:
                - id: Category slug (e.g., "en:cereals")
                - name: Display name
                - products: Number of products in this category
                - url: URL to browse this category
        """
        url = f"{self.base_url}/categories.json"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_labels_list(self) -> Dict[str, Any]:
        """
        Get the full list of available labels/certifications.

        Returns:
            Dictionary with count and tags list (id, name, products, url per tag).
        """
        url = f"{self.base_url}/labels.json"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_additives_list(self) -> Dict[str, Any]:
        """
        Get the full list of food additives tracked in the database.

        Returns:
            Dictionary with count and tags list (id, name, products, url per tag).
        """
        url = f"{self.base_url}/additives.json"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_nutriments_for_product(self, barcode: str) -> Dict[str, Any]:
        """
        Convenience method to retrieve only the nutritional values for a product.

        Args:
            barcode: Product barcode (e.g., "3017624010701")

        Returns:
            Dictionary of nutritional values per 100g and per serving, e.g.:
            {
                "energy-kcal_100g": 539,
                "fat_100g": 30.9,
                "saturated-fat_100g": 10.6,
                "carbohydrates_100g": 57.5,
                "sugars_100g": 56.3,
                "fiber_100g": 0.0,
                "proteins_100g": 6.3,
                "salt_100g": 0.107,
                "sodium_100g": 0.0107,
                ...
            }
            Returns an empty dict if the product is not found.
        """
        result = self.get_product_by_barcode(
            barcode,
            fields=["nutriments", "product_name", "serving_size", "nutrition_grades"]
        )
        if result.get("status") == 1:
            return result.get("product", {}).get("nutriments", {})
        return {}

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def print_product(product_data: Dict[str, Any]) -> None:
    """
    Print a formatted summary of a single product from get_product_by_barcode().

    Args:
        product_data: The full response dictionary from get_product_by_barcode()
    """
    if product_data.get("status") != 1:
        print("Product not found.")
        return

    product = product_data.get("product", {})
    print("\n" + "=" * 80)
    print(f"  {product.get('product_name', 'Unknown Product').title()}")
    print("=" * 80)
    print(f"  Brand(s):       {product.get('brands', 'N/A')}")
    print(f"  Quantity:       {product.get('quantity', 'N/A')}")
    print(f"  Serving Size:   {product.get('serving_size', 'N/A')}")
    print(f"  Categories:     {product.get('categories', 'N/A')[:80]}")
    print(f"  Nutri-Score:    {str(product.get('nutrition_grades', 'N/A')).upper()}")
    print(f"  NOVA Group:     {product.get('nova_group', 'N/A')}")
    print(f"  Eco-Score:      {str(product.get('ecoscore_grade', 'N/A')).upper()}")

    nutriments = product.get("nutriments", {})
    if nutriments:
        print("\n  Nutrition (per 100g):")
        fields_to_show = [
            ("energy-kcal_100g", "Energy (kcal)"),
            ("fat_100g",          "Fat (g)"),
            ("saturated-fat_100g","Saturated Fat (g)"),
            ("carbohydrates_100g","Carbohydrates (g)"),
            ("sugars_100g",       "Sugars (g)"),
            ("fiber_100g",        "Fiber (g)"),
            ("proteins_100g",     "Proteins (g)"),
            ("salt_100g",         "Salt (g)"),
        ]
        for key, label in fields_to_show:
            value = nutriments.get(key)
            if value is not None:
                print(f"    {label:<22} {value}")

    allergens = product.get("allergens", "")
    if allergens:
        print(f"\n  Allergens:      {allergens}")

    labels = product.get("labels", "")
    if labels:
        print(f"  Labels:         {labels[:80]}")

    image_url = product.get("image_front_url", "")
    if image_url:
        print(f"\n  Image:          {image_url}")

    print("=" * 80 + "\n")


def print_products(search_result: Dict[str, Any], max_display: int = 10) -> None:
    """
    Print a formatted summary of products from search_products() or similar methods.

    Args:
        search_result: The response dictionary from any search/list method
        max_display: Maximum number of products to display (default: 10)
    """
    products = search_result.get("products", [])
    total = search_result.get("count", len(products))

    if not products:
        print("No products found.")
        return

    print(f"\nShowing {min(len(products), max_display)} of {total} product(s):\n")
    print("=" * 80)

    for i, product in enumerate(products[:max_display], 1):
        name = product.get("product_name") or product.get("abbreviated_product_name") or "Unknown"
        brand = product.get("brands", "N/A")
        nutriscore = str(product.get("nutrition_grades", "N/A")).upper()
        nova = product.get("nova_group", "N/A")
        ecoscore = str(product.get("ecoscore_grade", "N/A")).upper()
        code = product.get("code", "N/A")

        print(f"\n{i:>2}. {name.title()}")
        print(f"    Brand:       {brand}")
        print(f"    Barcode:     {code}")
        print(f"    Nutri-Score: {nutriscore}  |  NOVA Group: {nova}  |  Eco-Score: {ecoscore}")

        nutriments = product.get("nutriments", {})
        if nutriments.get("energy-kcal_100g") is not None:
            print(f"    Energy:      {nutriments['energy-kcal_100g']} kcal/100g  |  "
                  f"Proteins: {nutriments.get('proteins_100g', 'N/A')}g  |  "
                  f"Sugar: {nutriments.get('sugars_100g', 'N/A')}g")

    print("\n" + "=" * 80)