import requests
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv


class ExerciseDBClient:
    # Shared timeout for all requests (seconds)
    _TIMEOUT = 10
    def __init__(self):
        """
        Initialize the ExerciseDB API client
        
        Loads API key from .env file. The .env file should contain:
        - EXERCISEDB_API_KEY=your_api_key_here
        - EXERCISEDB_API_HOST=exercisedb.p.rapidapi.com
        - EXERCISEDB_BASE_URL=https://exercisedb.p.rapidapi.com
        
        Raises:
            ValueError: If .env file is missing or API key is not set
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API credentials from environment
        self.api_key = os.getenv('EXERCISEDB_API_KEY')
        self.api_host = os.getenv('EXERCISEDB_API_HOST', 'exercisedb.p.rapidapi.com')
        self.base_url = os.getenv('EXERCISEDB_BASE_URL', 'https://exercisedb.p.rapidapi.com')
        
        # Validate that API key exists
        if not self.api_key:
            raise ValueError("EXERCISEDB_API_KEY not found in environment variables.")
        
        # Set up headers
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }

    def _get(self, url: str, params: dict = None):
        """
        Internal helper for GET requests with consistent timeout and error handling.
        Raises RuntimeError with a descriptive message on any network or HTTP failure.
        """
        try:
            response = requests.get(
                url, headers=self.headers, params=params or {}, timeout=self._TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise RuntimeError(f"ExerciseDB request timed out after {self._TIMEOUT}s: {url}")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"Could not connect to ExerciseDB: {url}")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"ExerciseDB returned HTTP {e.response.status_code}: {url}")
        except ValueError:
            raise RuntimeError(f"ExerciseDB returned invalid JSON: {url}")

    def get_all_exercises(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a list of all exercises
        
        Args:
            limit: Number of results to return (default: 10, max: 1000)
            offset: How many results to skip before starting to return data (default: 0)
            
        Returns:
            List of exercise dictionaries, each containing:
            - id: Exercise ID
            - name: Exercise name (e.g., "Barbell Bench Press")
            - bodyPart: Body part targeted (e.g., "chest")
            - target: Specific muscle targeted (e.g., "pectorals")
            - equipment: Equipment needed (e.g., "barbell")
            - gifUrl: URL to animated GIF demonstration (if available)
            - secondaryMuscles: List of secondary muscles worked
            - instructions: Step-by-step instructions list
        """
        url = f"{self.base_url}/exercises"
        params = {'limit': limit, 'offset': offset}
        return self._get(url, params)
    
    def get_exercise_by_id(self, exercise_id: str) -> Dict[str, Any]:
        """
        Get a specific exercise by its ID
        
        Args:
            exercise_id: The unique ID of the exercise (e.g., "0001")
            
        Returns:
            Dictionary containing complete exercise information:
            - id: Exercise ID
            - name: Exercise name
            - bodyPart: Body part targeted
            - target: Specific muscle targeted
            - equipment: Equipment needed
            - gifUrl: URL to animated GIF demonstration (if available)
            - secondaryMuscles: List of secondary muscles worked
            - instructions: Step-by-step instructions list
        """
        url = f"{self.base_url}/exercises/exercise/{exercise_id}"
        return self._get(url)
    
    def get_exercises_by_body_part(self, body_part: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get exercises filtered by body part
        
        Args:
            body_part: The body part to filter by. Valid options:
                      - back
                      - cardio
                      - chest
                      - lower arms
                      - lower legs
                      - neck
                      - shoulders
                      - upper arms
                      - upper legs
                      - waist
            limit: Number of results to return (default: 10, max: 1000)
            
        Returns:
            List of exercise dictionaries matching the body part filter.
            Each dictionary contains: id, name, bodyPart, target, equipment,
            gifUrl (if available), secondaryMuscles, instructions
        """
        url = f"{self.base_url}/exercises/bodyPart/{body_part}"
        params = {'limit': limit}
        return self._get(url, params)
    
    def get_exercises_by_target(self, target_muscle: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get exercises filtered by target muscle
        
        Args:
            target_muscle: The specific muscle to target. 
            limit: Number of results to return (default: 10, max: 1000)
            
        Returns:
            List of exercise dictionaries targeting the specified muscle.
            Each dictionary contains: id, name, bodyPart, target, equipment,
            gifUrl (if available), secondaryMuscles, instructions
        """
        url = f"{self.base_url}/exercises/target/{target_muscle}"
        params = {'limit': limit}
        return self._get(url, params)
    
    def get_exercises_by_equipment(self, equipment: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get exercises filtered by equipment type
        
        Args:
            equipment: The equipment type to filter by.
            limit: Number of results to return (default: 10, max: 1000)
            
        Returns:
            List of exercise dictionaries using the specified equipment.
            Each dictionary contains: id, name, bodyPart, target, equipment,
            gifUrl (if available), secondaryMuscles, instructions
        """
        url = f"{self.base_url}/exercises/equipment/{equipment}"
        params = {'limit': limit}
        return self._get(url, params)
    
    def search_by_name(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for exercises by name
        
        Args:
            name: The exercise name or partial name to search for (e.g., "bench", "curl")
            limit: Number of results to return (default: 10, max: 1000)
            
        Returns:
            List of exercise dictionaries matching the search term.
            Each dictionary contains: id, name, bodyPart, target, equipment,
            gifUrl (if available), secondaryMuscles, instructions
        """
        url = f"{self.base_url}/exercises/name/{name}"
        params = {'limit': limit}
        return self._get(url, params)
    
    def get_body_part_list(self) -> List[str]:
        """Get list of all available body parts"""
        url = f"{self.base_url}/exercises/bodyPartList"
        return self._get(url)
    
    def get_target_list(self) -> List[str]:
        """Get list of all target muscles"""
        url = f"{self.base_url}/exercises/targetList"
        return self._get(url)
    
    def get_equipment_list(self) -> List[str]:
        """Get list of all equipment types"""
        url = f"{self.base_url}/exercises/equipmentList"
        return self._get(url)


# Helper function to print exercises nicely
def print_exercises(exercises: List[Dict[str, Any]]) -> None:
    """
    Print a formatted summary of exercises
    
    Args:
        exercises: List of exercise dictionaries from any get method
    """
    if not exercises:
        print("No exercises found.")
        return
    
    print(f"\nFound {len(exercises)} exercise(s):\n")
    print("=" * 80)
    
    for i, ex in enumerate(exercises, 1):
        print(f"\n{i}. {ex.get('name', 'Unknown').title()}")
        print(f"   Body Part: {ex.get('bodyPart', 'N/A').title()}")
        print(f"   Target: {ex.get('target', 'N/A').title()}")
        print(f"   Equipment: {ex.get('equipment', 'N/A').title()}")
        
        # Handle different possible field names for GIF URL
        gif_url = ex.get('gifUrl') or ex.get('gif_url') or ex.get('image') or 'N/A'
        if gif_url != 'N/A':
            print(f"   GIF Demo: {gif_url}")
        
        # Print secondary muscles if available
        secondary = ex.get('secondaryMuscles', [])
        if secondary:
            print(f"   Secondary Muscles: {', '.join(secondary)}")
        
        # Print instructions if available
        instructions = ex.get('instructions', [])
        if instructions:
            print(f"   Instructions:")
            for step_num, step in enumerate(instructions[:3], 1):  # Show first 3 steps
                print(f"      {step_num}. {step}")
            if len(instructions) > 3:
                print(f"      ... ({len(instructions) - 3} more steps)")
    
    print("\n" + "=" * 80)