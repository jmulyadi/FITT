import { apiFetch } from "./clients";

const today = () => new Date().toISOString().split("T")[0];

// ── Meals ─────────────────────────────────────────────────────────────────────

export async function getTodaysMeals() {
  return apiFetch(`/meals/date/${today()}`);
}

export async function createMeal(mealNum, caloriesIn = 0) {
  return apiFetch("/meals/", {
    method: "POST",
    body: JSON.stringify({ date: today(), meal_num: mealNum, calories_in: caloriesIn }),
  });
}

export async function updateMealCalories(mealId, caloriesIn) {
  return apiFetch(`/meals/${mealId}`, {
    method: "PATCH",
    body: JSON.stringify({ calories_in: caloriesIn }),
  });
}

export async function deleteMeal(mealId) {
  return apiFetch(`/meals/${mealId}`, { method: "DELETE" });
}

// ── Food items ────────────────────────────────────────────────────────────────

export async function addFoodToMeal(mealId, name, foodType, calories) {
  return apiFetch(`/meals/${mealId}/food`, {
    method: "POST",
    body: JSON.stringify({ name, food_type: foodType, calories }),
  });
}

export async function updateFoodItem(mealId, foodId, calories) {
  return apiFetch(`/meals/${mealId}/food/${foodId}`, {
    method: "PATCH",
    body: JSON.stringify({ calories }),
  });
}

export async function deleteFoodItem(mealId, foodId) {
  return apiFetch(`/meals/${mealId}/food/${foodId}`, { method: "DELETE" });
}

export async function getMealsByDate(date) {
  return apiFetch(`/meals/date/${date}`);
}

// ── Food search (OpenFoodFacts) ───────────────────────────────────────────────

export async function searchFood(query, page = 1) {
  return apiFetch(`/meals/food-search/search?query=${encodeURIComponent(query)}&page=${page}&page_size=15`);
}