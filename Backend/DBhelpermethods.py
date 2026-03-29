from supabase import Client
from typing import Dict, Any, List


class FitnessBackend:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    # ============================================================================
    # SESSION HELPERS
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

    def get_user(self, username: str) -> Dict[str, Any]:
        response = self.supabase.table("USER").select("*").eq("username", username).execute()
        if not response.data:
            raise ValueError(f"User '{username}' not found.")
        return response.data[0]

    def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        response = self.supabase.table("USER").select("*").eq("id", user_id).execute()
        if not response.data:
            raise ValueError(f"User with id '{user_id}' not found.")
        return response.data[0]

    def update_user_profile(self, username: str, **kwargs) -> Dict[str, Any]:
        if not kwargs:
            raise ValueError("No fields provided for update.")
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

    def add_workout(self, date: str, duration: int, calories_burned: int,
                    workout_type: str, cardio_type: str = None,
                    distance: float = None) -> int:
        """
        Creates a new workout and links it to the current user via user_workout.
        Returns the new workout_id.
        """
        user_id = self.get_user_id_from_session()

        data = {
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

        workout_id = response.data[0]["workout_id"]

        # Link user to workout via junction table
        self.supabase.table("user_workout").insert({
            "user_id": user_id,
            "workout_id": workout_id,
            "date": date,
        }).execute()

        return workout_id

    def get_workout_by_id(self, workout_id: int) -> Dict[str, Any]:
        response = self.supabase.table("workout") \
            .select('*, exercise(*, "SET"(*))') \
            .eq("workout_id", workout_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Workout ID {workout_id} not found.")
        return response.data[0]

    def get_workouts_by_date(self, date_string: str) -> List[Dict[str, Any]]:
        """Fetches all workouts for the current user on a specific date."""
        user_id = self.get_user_id_from_session()

        junc = self.supabase.table("user_workout") \
            .select("workout_id, date") \
            .eq("user_id", user_id) \
            .eq("date", date_string) \
            .execute()

        if not junc.data:
            return []

        date_map = {r["workout_id"]: r["date"] for r in junc.data}
        workout_ids = list(date_map.keys())

        response = self.supabase.table("workout") \
            .select('*, exercise(*, "SET"(*))') \
            .in_("workout_id", workout_ids) \
            .execute()

        workouts = response.data or []
        for w in workouts:
            w.setdefault("date", date_map.get(w["workout_id"]))
        return workouts

    def get_all_workouts(self) -> List[Dict[str, Any]]:
        """Fetches all workouts for the current user, most recent first."""
        user_id = self.get_user_id_from_session()

        junc = self.supabase.table("user_workout") \
            .select("workout_id, date") \
            .eq("user_id", user_id) \
            .execute()

        if not junc.data:
            return []

        # Build a date lookup from junction table for sorting
        date_map = {r["workout_id"]: r["date"] for r in junc.data}
        workout_ids = list(date_map.keys())

        response = self.supabase.table("workout") \
            .select('*, exercise(*, "SET"(*))') \
            .in_("workout_id", workout_ids) \
            .execute()

        workouts = response.data or []
        for w in workouts:
            w.setdefault("date", date_map.get(w["workout_id"]))
        return sorted(workouts, key=lambda w: w["date"] or "", reverse=True)

    def get_workouts_in_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetches all workouts for the current user between two dates (inclusive)."""
        user_id = self.get_user_id_from_session()

        junc = self.supabase.table("user_workout") \
            .select("workout_id, date") \
            .eq("user_id", user_id) \
            .gte("date", start_date) \
            .lte("date", end_date) \
            .execute()

        if not junc.data:
            return []

        date_map = {r["workout_id"]: r["date"] for r in junc.data}
        workout_ids = list(date_map.keys())

        response = self.supabase.table("workout") \
            .select('*, exercise(*, "SET"(*))') \
            .in_("workout_id", workout_ids) \
            .execute()

        workouts = response.data or []
        for w in workouts:
            w.setdefault("date", date_map.get(w["workout_id"]))
        return sorted(workouts, key=lambda w: w["date"] or "", reverse=True)

    def update_workout(self, workout_id: int, **updates) -> Dict[str, Any]:
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
        # user_workout row deleted via CASCADE
        response = self.supabase.table("workout").delete().eq("workout_id", workout_id).execute()
        if not response.data:
            raise ValueError(f"Delete failed. Workout {workout_id} not found.")
        return response.data

    # ============================================================================
    # EXERCISE METHODS
    # ============================================================================

    def add_exercise(self, workout_id: int, name: str, muscle_group: str) -> int:
        data = {"workout_id": workout_id, "name": name, "muscle_group": muscle_group}
        response = self.supabase.table("exercise").insert(data).execute()
        if not response.data:
            raise RuntimeError(f"Failed to add exercise to workout {workout_id}.")
        return response.data[0]["exercise_id"]

    def get_exercise_by_id(self, exercise_id: int) -> Dict[str, Any]:
        response = self.supabase.table("exercise") \
            .select('*, "SET"(*)') \
            .eq("exercise_id", exercise_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Exercise ID {exercise_id} not found.")
        return response.data[0]

    def get_exercises_by_workout(self, workout_id: int) -> List[Dict[str, Any]]:
        response = self.supabase.table("exercise") \
            .select('*, "SET"(*)') \
            .eq("workout_id", workout_id) \
            .order("exercise_id") \
            .execute()
        if not response.data:
            raise ValueError(f"No exercises found for workout {workout_id}.")
        return response.data

    def update_exercise(self, exercise_id: int, **kwargs) -> Dict[str, Any]:
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
        response = self.supabase.table("exercise").delete().eq("exercise_id", exercise_id).execute()
        if not response.data:
            raise ValueError(f"Delete failed. Exercise ID {exercise_id} not found.")
        return response.data

    # ============================================================================
    # SET METHODS
    # ============================================================================

    def add_set(self, exercise_id: int, set_num: int, reps: int,
                weight: float, intensity: int) -> Dict[str, Any]:
        data = {
            "exercise_id": exercise_id,
            "set_num": set_num,
            "reps": reps,
            "weight": weight,
            "intensity": intensity,
        }
        response = self.supabase.table("SET").insert(data).execute()
        if not response.data:
            raise RuntimeError(f"Failed to add set to exercise {exercise_id}.")
        return response.data[0]

    def get_set_by_id(self, set_id: int) -> Dict[str, Any]:
        response = self.supabase.table("SET") \
            .select("*") \
            .eq("set_id", set_id) \
            .single() \
            .execute()
        if not response.data:
            raise ValueError(f"No set found with ID {set_id}.")
        return response.data

    def get_sets_by_exercise(self, exercise_id: int) -> List[Dict[str, Any]]:
        response = self.supabase.table("SET") \
            .select("*") \
            .eq("exercise_id", exercise_id) \
            .order("set_num", desc=False) \
            .execute()
        if not response.data:
            raise ValueError(f"No sets found for exercise {exercise_id}.")
        return response.data

    def update_set(self, set_id: int, **kwargs) -> Dict[str, Any]:
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
        response = self.supabase.table("SET").delete().eq("set_id", set_id).execute()
        if not response.data:
            raise ValueError(f"Delete failed. Set ID {set_id} not found.")
        return response.data

    # ============================================================================
    # MEAL METHODS
    # ============================================================================

    def add_meal(self, date: str, meal_num: int, calories_in: int) -> int:
        """
        Creates a new meal and links it to the current user via user_meal.
        Returns the new meal_id.
        """
        user_id = self.get_user_id_from_session()

        data = {"meal_num": meal_num, "calories_in": calories_in}
        response = self.supabase.table("meal").insert(data).execute()
        if not response.data:
            raise RuntimeError("Failed to log meal.")

        meal_id = response.data[0]["meal_id"]

        self.supabase.table("user_meal").insert({
            "user_id": user_id,
            "meal_id": meal_id,
            "date": date,
        }).execute()

        return meal_id

    def get_meal_by_id(self, meal_id: int) -> Dict[str, Any]:
        response = self.supabase.table("meal") \
            .select("*, food(*)") \
            .eq("meal_id", meal_id) \
            .execute()
        if not response.data:
            raise ValueError(f"Meal ID {meal_id} not found.")
        return response.data[0]

    def get_daily_meals(self, date_string: str) -> List[Dict[str, Any]]:
        """Fetches all meals for the current user on a specific date."""
        user_id = self.get_user_id_from_session()

        junc = self.supabase.table("user_meal") \
            .select("meal_id, date") \
            .eq("user_id", user_id) \
            .eq("date", date_string) \
            .execute()

        if not junc.data:
            return []

        date_map = {r["meal_id"]: r["date"] for r in junc.data}
        meal_ids = list(date_map.keys())

        response = self.supabase.table("meal") \
            .select("*, food(*)") \
            .in_("meal_id", meal_ids) \
            .order("meal_num", desc=False) \
            .execute()

        meals = response.data or []
        for m in meals:
            m.setdefault("date", date_map.get(m["meal_id"]))
        return meals

    def get_meals_in_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetches all meals for the current user between two dates (inclusive)."""
        user_id = self.get_user_id_from_session()

        junc = self.supabase.table("user_meal") \
            .select("meal_id, date") \
            .eq("user_id", user_id) \
            .gte("date", start_date) \
            .lte("date", end_date) \
            .execute()

        if not junc.data:
            return []

        meal_ids = [r["meal_id"] for r in junc.data]

        response = self.supabase.table("meal") \
            .select("*, food(*)") \
            .in_("meal_id", meal_ids) \
            .order("meal_num", desc=False) \
            .execute()

        meals = response.data or []
        date_map2 = {r["meal_id"]: r["date"] for r in junc.data}
        for m in meals:
            m.setdefault("date", date_map2.get(m["meal_id"]))
        return sorted(meals, key=lambda m: m["date"] or "", reverse=True)

    def update_meal(self, meal_id: int, **kwargs) -> Dict[str, Any]:
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
        response = self.supabase.table("meal").delete().eq("meal_id", meal_id).execute()
        if not response.data:
            raise ValueError(f"Delete failed. Meal ID {meal_id} not found.")
        return response.data

    # ============================================================================
    # FOOD METHODS
    # ============================================================================

    def add_food_to_meal(self, meal_id: int, name: str, food_type: str,
                         calories: int) -> Dict[str, Any]:
        data = {"meal_id": meal_id, "name": name, "type": food_type, "calories": calories}
        response = self.supabase.table("food").insert(data).execute()
        if not response.data:
            raise RuntimeError(f"Failed to add food to meal {meal_id}.")
        return response.data[0]

    def get_food_by_id(self, food_id: int) -> Dict[str, Any]:
        response = self.supabase.table("food") \
            .select("*") \
            .eq("food_id", food_id) \
            .single() \
            .execute()
        if not response.data:
            raise ValueError(f"No food found with ID {food_id}.")
        return response.data

    def get_foods_by_meal(self, meal_id: int) -> List[Dict[str, Any]]:
        response = self.supabase.table("food") \
            .select("*") \
            .eq("meal_id", meal_id) \
            .execute()
        if not response.data:
            raise ValueError(f"No food items found for meal {meal_id}.")
        return response.data

    def update_food(self, food_id: int, **kwargs) -> Dict[str, Any]:
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
        response = self.supabase.table("food").delete().eq("food_id", food_id).execute()
        if not response.data:
            raise ValueError(f"Delete failed. Food ID {food_id} not found.")
        return response.data

    # ============================================================================
    # ANALYTICS
    # ============================================================================

    def get_total_calories_burned(self, start_date: str, end_date: str) -> int:
        workouts = self.get_workouts_in_range(start_date, end_date)
        return sum(w.get("calories_burned", 0) for w in workouts)

    def get_total_calories_consumed(self, start_date: str, end_date: str) -> int:
        meals = self.get_meals_in_range(start_date, end_date)
        return sum(m.get("calories_in", 0) for m in meals)

    def get_net_calories(self, date_string: str) -> Dict[str, int]:
        workouts = self.get_workouts_by_date(date_string)
        calories_burned = sum(w.get("calories_burned", 0) for w in workouts)
        meals = self.get_daily_meals(date_string)
        calories_in = sum(m.get("calories_in", 0) for m in meals)
        return {
            "calories_in": calories_in,
            "calories_burned": calories_burned,
            "net_calories": calories_in - calories_burned,
        }

    def get_average_workout_duration(self, start_date: str, end_date: str) -> float:
        workouts = self.get_workouts_in_range(start_date, end_date)
        if not workouts:
            return 0.0
        return sum(w.get("duration", 0) for w in workouts) / len(workouts)

    def get_exercise_progress(self, exercise_name: str,
                              start_date: str, end_date: str) -> List[Dict[str, Any]]:
        workouts = self.get_workouts_in_range(start_date, end_date)
        progress = []
        for workout in workouts:
            try:
                exercises = self.get_exercises_by_workout(workout["workout_id"])
                for exercise in exercises:
                    if exercise["name"].lower() == exercise_name.lower():
                        sets = exercise.get("SET", [])
                        if sets:
                            max_weight = max(s.get("weight", 0) for s in sets)
                            total_volume = sum(s.get("weight", 0) * s.get("reps", 0) for s in sets)
                            progress.append({
                                "date": workout["date"],
                                "workout_id": workout["workout_id"],
                                "exercise_id": exercise["exercise_id"],
                                "max_weight": max_weight,
                                "total_volume": total_volume,
                                "num_sets": len(sets),
                            })
            except ValueError:
                continue
        return sorted(progress, key=lambda x: x["date"])

    def get_workout_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        workouts = self.get_workouts_in_range(start_date, end_date)
        if not workouts:
            return {
                "total_workouts": 0,
                "total_calories_burned": 0,
                "total_duration": 0,
                "average_duration": 0.0,
                "cardio_sessions": 0,
                "strength_sessions": 0,
            }
        total_calories = sum(w.get("calories_burned", 0) for w in workouts)
        total_duration = sum(w.get("duration", 0) for w in workouts)
        cardio_count = sum(1 for w in workouts if w.get("type") == "cardio")
        strength_count = sum(1 for w in workouts if w.get("type") == "strength")
        return {
            "total_workouts": len(workouts),
            "total_calories_burned": total_calories,
            "total_duration": total_duration,
            "average_duration": total_duration / len(workouts),
            "cardio_sessions": cardio_count,
            "strength_sessions": strength_count,
        }

    def get_nutrition_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        meals = self.get_meals_in_range(start_date, end_date)
        if not meals:
            return {
                "total_meals": 0,
                "total_calories": 0,
                "average_calories_per_day": 0.0,
                "average_calories_per_meal": 0.0,
            }
        total_calories = sum(m.get("calories_in", 0) for m in meals)
        unique_dates = set(m["date"] for m in meals)
        num_days = len(unique_dates)
        return {
            "total_meals": len(meals),
            "total_calories": total_calories,
            "average_calories_per_day": total_calories / num_days if num_days > 0 else 0.0,
            "average_calories_per_meal": total_calories / len(meals),
        }