from supabase import Client
from typing import Dict, Any, List


class FitnessBackend:
    def __init__(self, supabase_client: Client, user_id: str = None):
        """
        Initialize FitnessBackend with a shared, already-authenticated Supabase client.
        Args:
            supabase_client: An instance of supabase.Client with RLS token applied.
            user_id: The authenticated user's UUID (passed in from dependencies.py).
        """
        self.supabase = supabase_client
        self._user_id = user_id

    # ============================================================================
    # SESSION HELPER
    # ============================================================================

    def get_username_from_session(self) -> str:
        """
        Resolves the username of the currently authenticated user.
        Uses the user_id injected at construction time — no extra auth call needed.
        """
        if not self._user_id:
            raise PermissionError("No active session. Please sign in.")

        response = self.supabase.table("USER") \
            .select("username") \
            .eq("id", self._user_id) \
            .execute()

        if not response.data:
            raise ValueError("No profile found for current user.")

        return response.data[0]["username"]

    # ============================================================================
    # USER METHODS
    # ============================================================================

    def get_user(self, username: str) -> Dict[str, Any]:
        """
        Retrieves a user's profile information by username.
        
        Args:
            username: Username to lookup
            
        Returns:
            User profile data
        """
        response = self.supabase.table("USER").select("*").eq("username", username).execute()

        if not response.data:
            raise ValueError(f"User '{username}' not found.")

        return response.data[0]

    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves a user's profile information by their auth UUID.
        
        Args:
            user_id: Supabase auth UUID
            
        Returns:
            User profile data
        """
        response = self.supabase.table("USER").select("*").eq("id", user_id).execute()

        if not response.data:
            raise ValueError(f"User with id '{user_id}' not found.")

        return response.data[0]

    def update_user_profile(self, username: str, **kwargs) -> Dict[str, Any]:
        """
        Updates specific fields for a user.
        
        Args:
            username: Username to update
            **kwargs: Fields to update (age, gender, weight, height, experience_level, bmi)
            
        Returns:
            Updated user data

        """
        if not kwargs:
            raise ValueError("No fields provided for update.")

        # Prevent accidental overwrite of protected fields
        protected = {"id", "username"}
        invalid = protected & kwargs.keys()
        if invalid:
            raise ValueError(f"Cannot update protected fields: {invalid}")

        response = self.supabase.table("USER") \
            .update(kwargs) \
            .eq("username", username) \
            .execute()

        if not response.data:
            raise ValueError(f"Update failed. User '{username}' not found.")

        return response.data[0]

    # ============================================================================
    # WORKOUT METHODS
    # ============================================================================

    def add_workout(self, username: str, date: str, duration: int,
                    calories_burned: int, workout_type: str = "strength",
                    cardio_type: str = None, distance: float = None) -> int:
        """
        Creates a new workout session.

        Args:
            username: User performing the workout
            date: Date of workout (ISO format: 'YYYY-MM-DD')
            duration: Duration in minutes
            calories_burned: Total calories burned
            workout_type: 'strength' or 'cardio'
            cardio_type: e.g. 'running' (cardio only)
            distance: km covered (cardio only)

        Returns:
            workout_id of the created workout
        """
        if workout_type not in ("strength", "cardio"):
            raise ValueError("workout_type must be 'strength' or 'cardio'.")
        if workout_type == "cardio" and not cardio_type:
            raise ValueError("cardio_type is required for cardio workouts.")

        data = {
            "username": username,
            "date": date,
            "duration": duration,
            "calories_burned": calories_burned,
            "type": workout_type,
        }
        if cardio_type:
            data["cardio_type"] = cardio_type
        if distance is not None:
            data["distance"] = distance

        response = self.supabase.table("workout").insert(data).execute()

        if not response.data:
            raise RuntimeError("Failed to log workout.")

        return response.data[0]['workout_id']

    def get_workout_by_id(self, workout_id: int) -> Dict[str, Any]:
        """
        Fetches a specific workout by ID with all related data.
        
        Args:
            workout_id: Workout ID to fetch
            
        Returns:
            Workout data with cardio and strength details
        """
        response = self.supabase.table("workout") \
            .select('*, cardio(*), strength(exercise(*, "SET"(*)))') \
            .eq("workout_id", workout_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Workout ID {workout_id} not found.")

        return response.data[0]

    def get_workouts_by_date(self, username: str, date_string: str) -> List[Dict[str, Any]]:
        """
        Fetches all workouts for a specific user on a specific date.
        
        Args:
            username: User to query
            date_string: Date in ISO format ('YYYY-MM-DD')
            
        Returns:
            List of workouts with cardio and strength details
        """
        response = self.supabase.table("workout") \
            .select('*, cardio(*), strength(exercise(*, "SET"(*)))') \
            .eq("username", username) \
            .eq("date", date_string) \
            .execute()

        if not response.data:
            return []

        return response.data

    def get_all_workouts(self, username: str) -> List[Dict[str, Any]]:
        """
        Fetches all workouts ever logged by a user, ordered most recent first.
        
        Args:
            username: User to query
            
        Returns:
            List of all workouts
        """
        response = self.supabase.table("workout") \
            .select('*, exercise(*, "SET"(*))') \
            .eq("username", username) \
            .order("date", desc=True) \
            .execute()

        if not response.data:
            return []

        return response.data

    def get_workouts_in_range(self, username: str, start_date: str,
                              end_date: str) -> List[Dict[str, Any]]:
        """
        Fetches all workouts between two dates (inclusive).
        
        Args:
            username: User to query
            start_date: Start date (ISO format: 'YYYY-MM-DD')
            end_date: End date (ISO format: 'YYYY-MM-DD')
            
        Returns:
            List of workouts ordered by date (most recent first)
        """
        response = self.supabase.table("workout") \
            .select("*, cardio(workout_id), strength(workout_id)") \
            .eq("username", username) \
            .gte("date", start_date) \
            .lte("date", end_date) \
            .order("date", desc=True) \
            .execute()

        if not response.data:
            print(f"No workouts found between '{start_date}' and '{end_date}' for '{username}'.")
            return []

        return response.data

    def update_workout(self, workout_id: int, **updates) -> Dict[str, Any]:
        """
        Updates specific fields of a workout.
        
        Args:
            workout_id: Workout to update
            **updates: Fields to update (date, duration, calories_burned)
            
        Returns:
            Updated workout data
        """
        if not updates:
            raise ValueError("No fields provided for update.")

        response = self.supabase.table("workout") \
            .update(updates) \
            .eq("workout_id", workout_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Update failed. Workout {workout_id} may not exist.")

        return response.data[0]

    def delete_workout(self, workout_id: int) -> List[Dict[str, Any]]:
        """
        Removes a workout and all its associated cardio/strength/sets.
        
        Args:
            workout_id: Workout to delete
            
        Returns:
            Deleted workout data
        """
        response = self.supabase.table("workout").delete().eq("workout_id", workout_id).execute()

        if not response.data:
            raise ValueError(f"Delete failed. Workout {workout_id} not found.")

        return response.data

    # ============================================================================
    # CARDIO METHODS
    # ============================================================================

    def add_cardio(self, workout_id: int, cardio_type: str, distance: float) -> Dict[str, Any]:
        """
        Adds cardio details to a workout.
        
        Args:
            workout_id: Associated workout
            cardio_type: Type of cardio (e.g., 'running', 'cycling', 'swimming')
            distance: Distance covered
            
        Returns:
            Created cardio record
        """
        data = {
            "workout_id": workout_id,
            "cardio_type": cardio_type,
            "distance": distance
        }
        response = self.supabase.table("cardio").insert(data).execute()

        if not response.data:
            raise RuntimeError(f"Failed to add cardio to workout {workout_id}.")

        return response.data[0]

    def get_cardio_by_workout(self, workout_id: int) -> Dict[str, Any]:
        """
        Fetches cardio details for a specific workout.
        
        Args:
            workout_id: Workout to query
            
        Returns:
            Cardio data
        """
        response = self.supabase.table("cardio") \
            .select("*") \
            .eq("workout_id", workout_id) \
            .execute()

        if not response.data:
            raise ValueError(f"No cardio data found for workout {workout_id}.")

        return response.data[0]

    def get_cardio_workouts_by_date(self, username: str, date_string: str) -> List[Dict[str, Any]]:
        """
        Fetches only cardio workouts for a specific date.
        
        Args:
            username: User to query
            date_string: Date in ISO format ('YYYY-MM-DD')
            
        Returns:
            List of cardio workouts
        """
        response = self.supabase.table("workout") \
            .select("*, cardio!inner(*)") \
            .eq("username", username) \
            .eq("date", date_string) \
            .execute()

        if not response.data:
            return []

        return response.data

    def update_cardio(self, workout_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update cardio_type or distance for a specific workout.
        
        Args:
            workout_id: Workout to update
            **kwargs: Fields to update (cardio_type, distance)
            
        Returns:
            Updated cardio data
        """
        if not kwargs:
            raise ValueError("No fields provided for update.")

        response = self.supabase.table("cardio") \
            .update(kwargs) \
            .eq("workout_id", workout_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Update failed. Cardio for workout {workout_id} not found.")

        return response.data[0]

    def delete_cardio(self, workout_id: int) -> List[Dict[str, Any]]:
        """
        Removes cardio data from a workout.
        
        Args:
            workout_id: Workout to remove cardio from
            
        Returns:
            Deleted cardio data
        """
        response = self.supabase.table("cardio").delete().eq("workout_id", workout_id).execute()

        if not response.data:
            raise ValueError(f"Delete failed. Cardio for workout {workout_id} not found.")

        return response.data

    # ============================================================================
    # STRENGTH METHODS
    # ============================================================================

    def add_strength_session(self, workout_id: int) -> Dict[str, Any]:
        """
        Creates a strength training record for a workout.
        
        Args:
            workout_id: Associated workout
            
        Returns:
            Created strength record
        """
        data = {"workout_id": workout_id}
        response = self.supabase.table("strength").insert(data).execute()

        if not response.data:
            raise RuntimeError(f"Failed to add strength session to workout {workout_id}.")

        return response.data[0]

    def get_strength_by_workout(self, workout_id: int) -> Dict[str, Any]:
        """
        Fetches strength session details for a specific workout.
        
        Args:
            workout_id: Workout to query
            
        Returns:
            Strength session data with exercises and sets
        """
        response = self.supabase.table("strength") \
            .select('*, exercise(*, "SET"(*))') \
            .eq("workout_id", workout_id) \
            .execute()

        if not response.data:
            raise ValueError(f"No strength data found for workout {workout_id}.")

        return response.data[0]

    def get_strength_workouts_by_date(self, username: str, date_string: str) -> List[Dict[str, Any]]:
        """
        Fetches only strength workouts for a specific date.
        
        Args:
            username: User to query
            date_string: Date in ISO format ('YYYY-MM-DD')
            
        Returns:
            List of strength workouts with exercises and sets
        """
        response = self.supabase.table("workout") \
            .select('*, strength!inner(exercise(*, "SET"(*)))') \
            .eq("username", username) \
            .eq("date", date_string) \
            .execute()

        if not response.data:
            return []

        return response.data

    def delete_strength_session(self, workout_id: int) -> List[Dict[str, Any]]:
        """
        Removes strength training data from a workout.
        Cascade deletes all associated exercises and sets.
        
        Args:
            workout_id: Workout to remove strength session from
            
        Returns:
            Deleted strength data
        """
        response = self.supabase.table("strength").delete().eq("workout_id", workout_id).execute()

        if not response.data:
            raise ValueError(f"Delete failed. Strength for workout {workout_id} not found.")

        return response.data

    # ============================================================================
    # EXERCISE METHODS
    # ============================================================================

    def add_exercise(self, workout_id: int, name: str, muscle_group: str) -> int:
        """
        Adds an exercise to a strength workout.
        
        Args:
            workout_id: Associated workout (must have a strength record)
            name: Exercise name (e.g., 'Bench Press', 'Squat')
            muscle_group: Target muscle group (e.g., 'Chest', 'Legs')
            
        Returns:
            exercise_id of the created exercise
        """
        data = {
            "workout_id": workout_id,
            "name": name,
            "muscle_group": muscle_group
        }
        response = self.supabase.table("exercise").insert(data).execute()

        if not response.data:
            raise RuntimeError(f"Failed to add exercise to workout {workout_id}.")

        return response.data[0]['exercise_id']

    def get_exercise_by_id(self, exercise_id: int) -> Dict[str, Any]:
        """
        Fetches a specific exercise with all its sets.
        
        Args:
            exercise_id: Exercise to fetch
            
        Returns:
            Exercise data with sets
        """
        response = self.supabase.table("exercise") \
            .select('*, "SET"(*)') \
            .eq("exercise_id", exercise_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Exercise ID {exercise_id} not found.")

        return response.data[0]

    def get_exercises_by_workout(self, workout_id: int) -> List[Dict[str, Any]]:
        """
        Fetches all exercises performed during a specific workout session.
        
        Args:
            workout_id: Workout to query
            
        Returns:
            List of exercises with their sets
        """
        response = self.supabase.table("exercise") \
            .select('*, "SET"(*)') \
            .eq("workout_id", workout_id) \
            .order("exercise_id") \
            .execute()

        if not response.data:
            raise ValueError(f"No exercises found for workout {workout_id}.")

        return response.data

    def update_exercise(self, exercise_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update name or muscle_group of an exercise.
        
        Args:
            exercise_id: Exercise to update
            **kwargs: Fields to update (name, muscle_group)
            
        Returns:
            Updated exercise data
        """
        if not kwargs:
            raise ValueError("No fields provided for update.")

        response = self.supabase.table("exercise") \
            .update(kwargs) \
            .eq("exercise_id", exercise_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Update failed. Exercise ID {exercise_id} not found.")

        return response.data[0]

    def delete_exercise(self, exercise_id: int) -> List[Dict[str, Any]]:
        """
        Removes an exercise and cascade deletes all its sets.
        
        Args:
            exercise_id: Exercise to delete
            
        Returns:
            Deleted exercise data
        """
        response = self.supabase.table("exercise").delete().eq("exercise_id", exercise_id).execute()

        if not response.data:
            raise ValueError(f"Delete failed. Exercise ID {exercise_id} not found.")

        return response.data

    # ============================================================================
    # SET METHODS
    # ============================================================================

    def add_set(self, exercise_id: int, set_num: int, reps: int,
                weight: float, intensity: int) -> Dict[str, Any]:
        """
        Adds a set to an exercise.
        
        Args:
            exercise_id: Associated exercise
            set_num: Set number (1, 2, 3, etc.)
            reps: Number of repetitions
            weight: Weight used
            intensity: Intensity level as integer (e.g., 1=light, 2=moderate, 3=heavy)
            
        Returns:
            Created set data
        """
        data = {
            "exercise_id": exercise_id,
            "set_num": set_num,
            "reps": reps,
            "weight": weight,
            "intensity": intensity
        }
        response = self.supabase.table("SET").insert(data).execute()

        if not response.data:
            raise RuntimeError(f"Failed to add set to exercise {exercise_id}.")

        return response.data[0]

    def get_set_by_id(self, set_id: int) -> Dict[str, Any]:
        """
        Fetches a single specific set by its unique ID.
        
        Args:
            set_id: Set to fetch
            
        Returns:
            Set data
        """
        response = self.supabase.table("SET") \
            .select("*") \
            .eq("set_id", set_id) \
            .single() \
            .execute()

        if not response.data:
            raise ValueError(f"No set found with ID {set_id}.")

        return response.data

    def get_sets_by_exercise(self, exercise_id: int) -> List[Dict[str, Any]]:
        """
        Fetches all sets for a specific exercise, ordered by set number.
        
        Args:
            exercise_id: Exercise to query
            
        Returns:
            List of sets ordered by set_num
        """
        response = self.supabase.table("SET") \
            .select("*") \
            .eq("exercise_id", exercise_id) \
            .order("set_num", desc=False) \
            .execute()

        if not response.data:
            raise ValueError(f"No sets found for exercise {exercise_id}.")

        return response.data

    def update_set(self, set_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update reps, weight, or intensity for a specific set.
        
        Args:
            set_id: Set to update
            **kwargs: Fields to update (set_num, reps, weight, intensity)
            
        Returns:
            Updated set data
        """
        if not kwargs:
            raise ValueError("No fields provided for update.")

        response = self.supabase.table("SET") \
            .update(kwargs) \
            .eq("set_id", set_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Update failed. Set ID {set_id} not found.")

        return response.data[0]

    def delete_set(self, set_id: int) -> List[Dict[str, Any]]:
        """
        Removes a specific set by its ID.
        
        Args:
            set_id: Set to delete
            
        Returns:
            Deleted set data
        """
        response = self.supabase.table("SET").delete().eq("set_id", set_id).execute()

        if not response.data:
            raise ValueError(f"Delete failed. Set ID {set_id} not found.")

        return response.data

    # ============================================================================
    # MEAL METHODS
    # ============================================================================

    def add_meal(self, username: str, date: str, meal_num: int,
                 calories_in: int) -> int:
        """
        Logs a meal entry.
        
        Args:
            username: User logging the meal
            date: Date of meal (ISO format: 'YYYY-MM-DD')
            meal_num: Meal number (1=Breakfast, 2=Lunch, 3=Dinner, etc.)
            calories_in: Total calories for this meal
            
        Returns:
            meal_id of the created meal
        """
        data = {
            "username": username,
            "date": date,
            "meal_num": meal_num,
            "calories_in": calories_in
        }
        response = self.supabase.table("meal").insert(data).execute()

        if not response.data:
            raise RuntimeError("Failed to log meal.")

        return response.data[0]['meal_id']

    def get_meal_by_id(self, meal_id: int) -> Dict[str, Any]:
        """
        Fetches a specific meal with all food items.
        
        Args:
            meal_id: Meal to fetch
            
        Returns:
            Meal data with food items
        """
        response = self.supabase.table("meal") \
            .select("*, food(*)") \
            .eq("meal_id", meal_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Meal ID {meal_id} not found.")

        return response.data[0]

    def get_daily_meals(self, username: str, date_string: str) -> List[Dict[str, Any]]:
        """
        Fetches all meals and their food items for a specific date.
        
        Args:
            username: User to query
            date_string: Date in ISO format ('YYYY-MM-DD')
            
        Returns:
            List of meals with food items, ordered by meal_num
        """
        response = self.supabase.table("meal") \
            .select("*, food(*)") \
            .eq("username", username) \
            .eq("date", date_string) \
            .order("meal_num", desc=False) \
            .execute()

        if not response.data:
            return []

        return response.data

    def get_meals_in_range(self, username: str, start_date: str,
                           end_date: str) -> List[Dict[str, Any]]:
        """
        Fetches all meals and associated food items between two dates (inclusive).
        
        Args:
            username: User to query
            start_date: Start date (ISO format: 'YYYY-MM-DD')
            end_date: End date (ISO format: 'YYYY-MM-DD')
            
        Returns:
            List of meals with food items
        """
        response = self.supabase.table("meal") \
            .select("*, food(*)") \
            .eq("username", username) \
            .gte("date", start_date) \
            .lte("date", end_date) \
            .order("date", desc=True) \
            .order("meal_num", desc=False) \
            .execute()

        if not response.data:
            return []

        return response.data

    def update_meal(self, meal_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update meal_num or calories_in for a meal.
        
        Args:
            meal_id: Meal to update
            **kwargs: Fields to update (meal_num, calories_in)
            
        Returns:
            Updated meal data
        """
        if not kwargs:
            raise ValueError("No fields provided for update.")

        response = self.supabase.table("meal") \
            .update(kwargs) \
            .eq("meal_id", meal_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Update failed. Meal ID {meal_id} not found.")

        return response.data[0]

    def delete_meal(self, meal_id: int) -> List[Dict[str, Any]]:
        """
        Removes a specific meal and its associated food entries.
        
        Args:
            meal_id: Meal to delete
            
        Returns:
            Deleted meal data
        """
        response = self.supabase.table("meal").delete().eq("meal_id", meal_id).execute()

        if not response.data:
            raise ValueError(f"Delete failed. Meal ID {meal_id} not found.")

        return response.data

    # ============================================================================
    # FOOD METHODS
    # ============================================================================

    def add_food_to_meal(self, meal_id: int, name: str, food_type: str,
                         calories: int) -> Dict[str, Any]:
        """
        Adds a specific food item to an existing meal.
        
        Args:
            meal_id: Associated meal
            name: Food name (e.g., 'Chicken Breast', 'Brown Rice')
            food_type: Type of food (e.g., 'Protein', 'Carbs', 'Vegetable')
            calories: Calories for this food item
            
        Returns:
            Created food data
        """
        data = {
            "meal_id": meal_id,
            "name": name,
            "type": food_type,
            "calories": calories
        }
        response = self.supabase.table("food").insert(data).execute()

        if not response.data:
            raise RuntimeError(f"Failed to add food to meal {meal_id}.")

        return response.data[0]

    def get_food_by_id(self, food_id: int) -> Dict[str, Any]:
        """
        Fetches a single food item's details.
        
        Args:
            food_id: Food to fetch
            
        Returns:
            Food data
        """
        response = self.supabase.table("food") \
            .select("*") \
            .eq("food_id", food_id) \
            .single() \
            .execute()

        if not response.data:
            raise ValueError(f"No food found with ID {food_id}.")

        return response.data

    def get_foods_by_meal(self, meal_id: int) -> List[Dict[str, Any]]:
        """
        Fetches all food items associated with a specific meal.
        
        Args:
            meal_id: Meal to query
            
        Returns:
            List of food items
        """
        response = self.supabase.table("food") \
            .select("*") \
            .eq("meal_id", meal_id) \
            .execute()

        if not response.data:
            raise ValueError(f"No food items found for meal {meal_id}.")

        return response.data

    def update_food(self, food_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update name, type, or calories of a specific food item.
        
        Args:
            food_id: Food to update
            **kwargs: Fields to update (name, type, calories)
            
        Returns:
            Updated food data
        """
        if not kwargs:
            raise ValueError("No fields provided for update.")

        response = self.supabase.table("food") \
            .update(kwargs) \
            .eq("food_id", food_id) \
            .execute()

        if not response.data:
            raise ValueError(f"Update failed. Food ID {food_id} not found.")

        return response.data[0]

    def delete_food_item(self, food_id: int) -> List[Dict[str, Any]]:
        """
        Removes a single food item from a meal.
        
        Args:
            food_id: Food to delete
            
        Returns:
            Deleted food data
        """
        response = self.supabase.table("food").delete().eq("food_id", food_id).execute()

        if not response.data:
            raise ValueError(f"Delete failed. Food ID {food_id} not found.")

        return response.data

    # ============================================================================
    # ANALYTICS & AGGREGATE METHODS
    # ============================================================================

    def get_total_calories_burned(self, username: str, start_date: str,
                                  end_date: str) -> int:
        """
        Calculates total calories burned over a date range.
        
        Args:
            username: User to query
            start_date: Start date (ISO format: 'YYYY-MM-DD')
            end_date: End date (ISO format: 'YYYY-MM-DD')
            
        Returns:
            Total calories burned
        """
        workouts = self.get_workouts_in_range(username, start_date, end_date)
        return sum(w.get('calories_burned', 0) for w in workouts)

    def get_total_calories_consumed(self, username: str, start_date: str,
                                    end_date: str) -> int:
        """
        Calculates total calories consumed over a date range.
        
        Args:
            username: User to query
            start_date: Start date (ISO format: 'YYYY-MM-DD')
            end_date: End date (ISO format: 'YYYY-MM-DD')
            
        Returns:
            Total calories consumed
        """
        meals = self.get_meals_in_range(username, start_date, end_date)
        return sum(m.get('calories_in', 0) for m in meals)

    def get_net_calories(self, username: str, date_string: str) -> Dict[str, int]:
        """
        Calculates net calories (consumed - burned) for a specific date.
        
        Args:
            username: User to query
            date_string: Date in ISO format ('YYYY-MM-DD')
            
        Returns:
            Dictionary with calories_in, calories_burned, and net_calories
        """
        workouts = self.get_workouts_by_date(username, date_string)
        calories_burned = sum(w.get('calories_burned', 0) for w in workouts)

        meals = self.get_daily_meals(username, date_string)
        calories_in = sum(m.get('calories_in', 0) for m in meals)

        return {
            'calories_in': calories_in,
            'calories_burned': calories_burned,
            'net_calories': calories_in - calories_burned
        }

    def get_average_workout_duration(self, username: str, start_date: str,
                                     end_date: str) -> float:
        """
        Calculates average workout duration over a date range.
        
        Args:
            username: User to query
            start_date: Start date (ISO format: 'YYYY-MM-DD')
            end_date: End date (ISO format: 'YYYY-MM-DD')
            
        Returns:
            Average duration in minutes
        """
        workouts = self.get_workouts_in_range(username, start_date, end_date)

        if not workouts:
            return 0.0

        total_duration = sum(w.get('duration', 0) for w in workouts)
        return total_duration / len(workouts)

    def get_exercise_progress(self, username: str, exercise_name: str,
                              start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Tracks progress for a specific exercise over time.
        Shows max weight and total volume per workout session.
        
        Args:
            username: User to query
            exercise_name: Name of exercise to track
            start_date: Start date (ISO format: 'YYYY-MM-DD')
            end_date: End date (ISO format: 'YYYY-MM-DD')
            
        Returns:
            List of workout sessions with exercise stats, sorted by date
        """
        workouts = self.get_workouts_in_range(username, start_date, end_date)
        progress = []

        for workout in workouts:
            try:
                exercises = self.get_exercises_by_workout(workout['workout_id'])

                for exercise in exercises:
                    if exercise['name'].lower() == exercise_name.lower():
                        sets = exercise.get('SET', [])

                        if sets:
                            max_weight = max(s.get('weight', 0) for s in sets)
                            total_volume = sum(s.get('weight', 0) * s.get('reps', 0) for s in sets)

                            progress.append({
                                'date': workout['date'],
                                'workout_id': workout['workout_id'],
                                'exercise_id': exercise['exercise_id'],
                                'max_weight': max_weight,
                                'total_volume': total_volume,
                                'num_sets': len(sets)
                            })
            except ValueError:
                continue

        return sorted(progress, key=lambda x: x['date'])

    def get_workout_summary(self, username: str, start_date: str,
                            end_date: str) -> Dict[str, Any]:
        """
        Generates a comprehensive workout summary for a date range.
        
        Args:
            username: User to query
            start_date: Start date (ISO format: 'YYYY-MM-DD')
            end_date: End date (ISO format: 'YYYY-MM-DD')
            
        Returns:
            Dictionary with summary statistics
        """
        workouts = self.get_workouts_in_range(username, start_date, end_date)

        if not workouts:
            return {
                'total_workouts': 0,
                'total_calories_burned': 0,
                'total_duration': 0,
                'average_duration': 0.0,
                'cardio_sessions': 0,
                'strength_sessions': 0
            }

        total_calories = sum(w.get('calories_burned', 0) for w in workouts)
        total_duration = sum(w.get('duration', 0) for w in workouts)

        # cardio/strength data is already embedded in each workout row â€” no extra queries needed
        cardio_count = sum(1 for w in workouts if w.get('cardio'))
        strength_count = sum(1 for w in workouts if w.get('strength'))

        return {
            'total_workouts': len(workouts),
            'total_calories_burned': total_calories,
            'total_duration': total_duration,
            'average_duration': total_duration / len(workouts),
            'cardio_sessions': cardio_count,
            'strength_sessions': strength_count
        }

    def get_nutrition_summary(self, username: str, start_date: str,
                              end_date: str) -> Dict[str, Any]:
        """
        Generates a comprehensive nutrition summary for a date range.
        
        Args:
            username: User to query
            start_date: Start date (ISO format: 'YYYY-MM-DD')
            end_date: End date (ISO format: 'YYYY-MM-DD')
            
        Returns:
            Dictionary with nutrition statistics
        """
        meals = self.get_meals_in_range(username, start_date, end_date)

        if not meals:
            return {
                'total_meals': 0,
                'total_calories': 0,
                'average_calories_per_day': 0.0,
                'average_calories_per_meal': 0.0
            }

        total_calories = sum(m.get('calories_in', 0) for m in meals)
        unique_dates = set(m['date'] for m in meals)
        num_days = len(unique_dates)

        return {
            'total_meals': len(meals),
            'total_calories': total_calories,
            'average_calories_per_day': total_calories / num_days if num_days > 0 else 0.0,
            'average_calories_per_meal': total_calories / len(meals) if len(meals) > 0 else 0.0
        }