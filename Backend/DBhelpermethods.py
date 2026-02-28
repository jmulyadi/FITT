from supabase import Client
from typing import Dict, Any, List, Optional


class FitnessBackend:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    # ============================================================================
    # SESSION HELPER
    # ============================================================================

    def get_user_id_from_session(self) -> str:
        """Returns the auth UUID of the currently signed-in user."""
        user = self.supabase.auth.get_user()
        if not user or not user.user:
            raise PermissionError("No active session. Please sign in.")
        return user.user.id

    def get_username_from_session(self) -> str:
        """Returns the username of the currently signed-in user."""
        user_id = self.get_user_id_from_session()
        response = self.supabase.table("USER") \
            .select("username") \
            .eq("id", user_id) \
            .execute()
        if not response.data:
            raise ValueError("No profile found for current user.")
        return response.data[0]["username"]

    # ============================================================================
    # USER METHODS
    # ============================================================================

    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Retrieves a user's profile by their auth UUID."""
        response = self.supabase.table("USER").select("*").eq("id", user_id).execute()
        if not response.data:
            raise ValueError(f"User '{user_id}' not found.")
        return response.data[0]

    def update_user_profile(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Updates allowed profile fields for a user."""
        if not kwargs:
            raise ValueError("No fields provided for update.")
        protected = {"id", "username"}
        invalid = protected & kwargs.keys()
        if invalid:
            raise ValueError(f"Cannot update protected fields: {invalid}")
        response = self.supabase.table("USER") \
            .update(kwargs) \
            .eq("id", user_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Update failed. User '{user_id}' not found.")
        return response.data[0]

    # ============================================================================
    # WORKOUT METHODS
    # ============================================================================

    def add_workout(self, username: str, date: str, duration: int,
                    calories_burned: int, workout_type: str,
                    cardio_type: Optional[str] = None,
                    distance: Optional[float] = None) -> int:
        """
        Creates a new workout session.
        workout_type: 'cardio' or 'strength'
        cardio_type and distance are required when workout_type is 'cardio'.
        """
        if workout_type == "cardio" and (not cardio_type or distance is None):
            raise ValueError("cardio_type and distance are required for cardio workouts.")

        data = {
            "username": username,
            "date": date,
            "duration": duration,
            "calories_burned": calories_burned,
            "type": workout_type,
        }
        if workout_type == "cardio":
            data["cardio_type"] = cardio_type
            data["distance"] = distance

        response = self.supabase.table("workout").insert(data).execute()
        if not response.data:
            raise RuntimeError("Failed to log workout.")
        return response.data[0]["workout_id"]

    def get_workout_by_id(self, workout_id: int) -> Dict[str, Any]:
        """Fetches a workout with all nested exercises and sets."""
        response = self.supabase.table("workout") \
            .select('*, exercise(*, "SET"(*))') \
            .eq("workout_id", workout_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Workout {workout_id} not found.")
        return response.data[0]

    def get_all_workouts(self, username: str) -> List[Dict[str, Any]]:
        """Fetches all workouts for a user, most recent first."""
        response = self.supabase.table("workout") \
            .select("*") \
            .eq("username", username) \
            .order("date", desc=True) \
            .execute()
        return response.data or []

    def get_workouts_by_date(self, username: str, date_string: str) -> List[Dict[str, Any]]:
        """Fetches all workouts for a user on a specific date."""
        response = self.supabase.table("workout") \
            .select('*, exercise(*, "SET"(*))') \
            .eq("username", username) \
            .eq("date", date_string) \
            .execute()
        return response.data or []

    def get_workouts_in_range(self, username: str, start_date: str,
                              end_date: str) -> List[Dict[str, Any]]:
        """Fetches all workouts between two dates (inclusive)."""
        response = self.supabase.table("workout") \
            .select("*") \
            .eq("username", username) \
            .gte("date", start_date) \
            .lte("date", end_date) \
            .order("date", desc=True) \
            .execute()
        return response.data or []

    def update_workout(self, workout_id: int, **updates) -> Dict[str, Any]:
        """Updates fields on a workout."""
        if not updates:
            raise ValueError("No fields provided for update.")
        response = self.supabase.table("workout") \
            .update(updates) \
            .eq("workout_id", workout_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Workout {workout_id} not found.")
        return response.data[0]

    def delete_workout(self, workout_id: int) -> List[Dict[str, Any]]:
        """Deletes a workout and all its exercises and sets via CASCADE."""
        response = self.supabase.table("workout").delete().eq("workout_id", workout_id).execute()
        if not response.data:
            raise ValueError(f"Workout {workout_id} not found.")
        return response.data

    # ============================================================================
    # EXERCISE METHODS
    # ============================================================================

    def add_exercise(self, workout_id: int, name: str, muscle_group: str) -> int:
        """Adds an exercise to a strength workout."""
        data = {
            "workout_id": workout_id,
            "name": name,
            "muscle_group": muscle_group
        }
        response = self.supabase.table("exercise").insert(data).execute()
        if not response.data:
            raise RuntimeError(f"Failed to add exercise to workout {workout_id}.")
        return response.data[0]["exercise_id"]

    def get_exercise_by_id(self, exercise_id: int) -> Dict[str, Any]:
        """Fetches a specific exercise with all its sets."""
        response = self.supabase.table("exercise") \
            .select('*, "SET"(*)') \
            .eq("exercise_id", exercise_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Exercise {exercise_id} not found.")
        return response.data[0]

    def get_exercises_by_workout(self, workout_id: int) -> List[Dict[str, Any]]:
        """Fetches all exercises for a workout with their sets."""
        response = self.supabase.table("exercise") \
            .select('*, "SET"(*)') \
            .eq("workout_id", workout_id) \
            .order("exercise_id") \
            .execute()
        return response.data or []

    def update_exercise(self, exercise_id: int, **kwargs) -> Dict[str, Any]:
        """Updates name or muscle_group of an exercise."""
        if not kwargs:
            raise ValueError("No fields provided for update.")
        response = self.supabase.table("exercise") \
            .update(kwargs) \
            .eq("exercise_id", exercise_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Exercise {exercise_id} not found.")
        return response.data[0]

    def delete_exercise(self, exercise_id: int) -> List[Dict[str, Any]]:
        """Deletes an exercise and all its sets via CASCADE."""
        response = self.supabase.table("exercise").delete().eq("exercise_id", exercise_id).execute()
        if not response.data:
            raise ValueError(f"Exercise {exercise_id} not found.")
        return response.data

    # ============================================================================
    # SET METHODS
    # ============================================================================

    def add_set(self, exercise_id: int, set_num: int, reps: int,
                weight: float, intensity: int) -> Dict[str, Any]:
        """Adds a set to an exercise."""
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
        """Fetches a single set by ID."""
        response = self.supabase.table("SET") \
            .select("*") \
            .eq("set_id", set_id) \
            .single() \
            .execute()
        if not response.data:
            raise ValueError(f"Set {set_id} not found.")
        return response.data

    def get_sets_by_exercise(self, exercise_id: int) -> List[Dict[str, Any]]:
        """Fetches all sets for an exercise, ordered by set number."""
        response = self.supabase.table("SET") \
            .select("*") \
            .eq("exercise_id", exercise_id) \
            .order("set_num") \
            .execute()
        return response.data or []

    def update_set(self, set_id: int, **kwargs) -> Dict[str, Any]:
        """Updates fields on a set."""
        if not kwargs:
            raise ValueError("No fields provided for update.")
        response = self.supabase.table("SET") \
            .update(kwargs) \
            .eq("set_id", set_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Set {set_id} not found.")
        return response.data[0]

    def delete_set(self, set_id: int) -> List[Dict[str, Any]]:
        """Deletes a set."""
        response = self.supabase.table("SET").delete().eq("set_id", set_id).execute()
        if not response.data:
            raise ValueError(f"Set {set_id} not found.")
        return response.data

    # ============================================================================
    # MEAL METHODS
    # ============================================================================

    def add_meal(self, username: str, date: str, meal_num: int,
                 calories_in: int) -> int:
        """Logs a meal entry."""
        data = {
            "username": username,
            "date": date,
            "meal_num": meal_num,
            "calories_in": calories_in
        }
        response = self.supabase.table("meal").insert(data).execute()
        if not response.data:
            raise RuntimeError("Failed to log meal.")
        return response.data[0]["meal_id"]

    def get_meal_by_id(self, meal_id: int) -> Dict[str, Any]:
        """Fetches a meal with all its food items."""
        response = self.supabase.table("meal") \
            .select("*, food(*)") \
            .eq("meal_id", meal_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Meal {meal_id} not found.")
        return response.data[0]

    def get_daily_meals(self, username: str, date_string: str) -> List[Dict[str, Any]]:
        """Fetches all meals and food items for a specific date."""
        response = self.supabase.table("meal") \
            .select("*, food(*)") \
            .eq("username", username) \
            .eq("date", date_string) \
            .order("meal_num") \
            .execute()
        return response.data or []

    def get_meals_in_range(self, username: str, start_date: str,
                           end_date: str) -> List[Dict[str, Any]]:
        """Fetches all meals between two dates (inclusive)."""
        response = self.supabase.table("meal") \
            .select("*, food(*)") \
            .eq("username", username) \
            .gte("date", start_date) \
            .lte("date", end_date) \
            .order("date", desc=True) \
            .execute()
        return response.data or []

    def update_meal(self, meal_id: int, **kwargs) -> Dict[str, Any]:
        """Updates fields on a meal."""
        if not kwargs:
            raise ValueError("No fields provided for update.")
        response = self.supabase.table("meal") \
            .update(kwargs) \
            .eq("meal_id", meal_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Meal {meal_id} not found.")
        return response.data[0]

    def delete_meal(self, meal_id: int) -> List[Dict[str, Any]]:
        """Deletes a meal and all its food items via CASCADE."""
        response = self.supabase.table("meal").delete().eq("meal_id", meal_id).execute()
        if not response.data:
            raise ValueError(f"Meal {meal_id} not found.")
        return response.data

    # ============================================================================
    # FOOD METHODS
    # ============================================================================

    def add_food_to_meal(self, meal_id: int, name: str, food_type: str,
                         calories: int) -> Dict[str, Any]:
        """Adds a food item to a meal."""
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
        """Fetches a single food item."""
        response = self.supabase.table("food") \
            .select("*") \
            .eq("food_id", food_id) \
            .single() \
            .execute()
        if not response.data:
            raise ValueError(f"Food {food_id} not found.")
        return response.data

    def get_foods_by_meal(self, meal_id: int) -> List[Dict[str, Any]]:
        """Fetches all food items for a meal."""
        response = self.supabase.table("food") \
            .select("*") \
            .eq("meal_id", meal_id) \
            .execute()
        return response.data or []

    def update_food(self, food_id: int, **kwargs) -> Dict[str, Any]:
        """Updates fields on a food item."""
        if not kwargs:
            raise ValueError("No fields provided for update.")
        response = self.supabase.table("food") \
            .update(kwargs) \
            .eq("food_id", food_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Food {food_id} not found.")
        return response.data[0]

    def delete_food_item(self, food_id: int) -> List[Dict[str, Any]]:
        """Deletes a food item."""
        response = self.supabase.table("food").delete().eq("food_id", food_id).execute()
        if not response.data:
            raise ValueError(f"Food {food_id} not found.")
        return response.data

    # ============================================================================
    # ANALYTICS
    # ============================================================================

    def get_net_calories(self, username: str, date_string: str) -> Dict[str, int]:
        """Returns calories consumed vs burned for a date."""
        workouts = self.get_workouts_by_date(username, date_string)
        calories_burned = sum(w.get("calories_burned", 0) for w in workouts)
        meals = self.get_daily_meals(username, date_string)
        calories_in = sum(m.get("calories_in", 0) for m in meals)
        return {
            "calories_in": calories_in,
            "calories_burned": calories_burned,
            "net_calories": calories_in - calories_burned
        }

    def get_total_calories_burned(self, username: str, start_date: str,
                                  end_date: str) -> int:
        """Total calories burned across workouts in a date range."""
        workouts = self.get_workouts_in_range(username, start_date, end_date)
        return sum(w.get("calories_burned", 0) for w in workouts)

    def get_total_calories_consumed(self, username: str, start_date: str,
                                    end_date: str) -> int:
        """Total calories consumed across meals in a date range."""
        meals = self.get_meals_in_range(username, start_date, end_date)
        return sum(m.get("calories_in", 0) for m in meals)

    def get_average_workout_duration(self, username: str, start_date: str,
                                     end_date: str) -> float:
        """Average workout duration in minutes across a date range."""
        workouts = self.get_workouts_in_range(username, start_date, end_date)
        if not workouts:
            return 0.0
        return sum(w.get("duration", 0) for w in workouts) / len(workouts)

    def get_workout_summary(self, username: str, start_date: str,
                            end_date: str) -> Dict[str, Any]:
        """Comprehensive workout summary for a date range."""
        workouts = self.get_workouts_in_range(username, start_date, end_date)
        if not workouts:
            return {
                "total_workouts": 0,
                "total_calories_burned": 0,
                "total_duration": 0,
                "average_duration": 0.0,
                "cardio_sessions": 0,
                "strength_sessions": 0
            }
        total_calories = sum(w.get("calories_burned", 0) for w in workouts)
        total_duration = sum(w.get("duration", 0) for w in workouts)
        return {
            "total_workouts": len(workouts),
            "total_calories_burned": total_calories,
            "total_duration": total_duration,
            "average_duration": total_duration / len(workouts),
            "cardio_sessions": sum(1 for w in workouts if w.get("type") == "cardio"),
            "strength_sessions": sum(1 for w in workouts if w.get("type") == "strength")
        }

    def get_nutrition_summary(self, username: str, start_date: str,
                              end_date: str) -> Dict[str, Any]:
        """Comprehensive nutrition summary for a date range."""
        meals = self.get_meals_in_range(username, start_date, end_date)
        if not meals:
            return {
                "total_meals": 0,
                "total_calories": 0,
                "average_calories_per_day": 0.0,
                "average_calories_per_meal": 0.0
            }
        total_calories = sum(m.get("calories_in", 0) for m in meals)
        num_days = len(set(m["date"] for m in meals))
        return {
            "total_meals": len(meals),
            "total_calories": total_calories,
            "average_calories_per_day": total_calories / num_days if num_days > 0 else 0.0,
            "average_calories_per_meal": total_calories / len(meals)
        }

    def get_exercise_progress(self, username: str, exercise_name: str,
                              start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Tracks max weight and total volume for an exercise over time."""
        workouts = self.get_workouts_in_range(username, start_date, end_date)
        progress = []
        for workout in workouts:
            exercises = self.get_exercises_by_workout(workout["workout_id"])
            for exercise in exercises:
                if exercise["name"].lower() == exercise_name.lower():
                    sets = exercise.get("SET", [])
                    if sets:
                        progress.append({
                            "date": workout["date"],
                            "workout_id": workout["workout_id"],
                            "exercise_id": exercise["exercise_id"],
                            "max_weight": max(s.get("weight", 0) for s in sets),
                            "total_volume": sum(s.get("weight", 0) * s.get("reps", 0) for s in sets),
                            "num_sets": len(sets)
                        })
        return sorted(progress, key=lambda x: x["date"])