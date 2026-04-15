import { apiFetch } from "./clients";

function getUserIdFromToken() {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("Not authenticated");
  // JWT payload is the middle segment, base64url encoded
  const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
  return payload.sub; // Supabase puts the user UUID in the 'sub' claim
}

export async function getMyProfile() {
  const userId = getUserIdFromToken();
  return apiFetch(`/users/${userId}`);
}

export async function getWorkoutsInRange(startDate, endDate) {
  return apiFetch(`/workouts/?start_date=${startDate}&end_date=${endDate}`);
}

export async function getMealsByDate(date) {
  return apiFetch(`/meals/date/${date}`);
}

export async function getWorkoutSummary(startDate, endDate) {
  return apiFetch(`/workouts/analytics/summary?start_date=${startDate}&end_date=${endDate}`);
}

export async function getNetCalories(date) {
  return apiFetch(`/workouts/analytics/net-calories/${date}`);
}

export async function getCaloriesBurned(startDate, endDate) {
  return apiFetch(`/workouts/analytics/calories-burned?start_date=${startDate}&end_date=${endDate}`);
}

export async function getExerciseProgress(exerciseName, startDate, endDate) {
  return apiFetch(`/workouts/analytics/progress/${encodeURIComponent(exerciseName)}?start_date=${startDate}&end_date=${endDate}`);
}

export async function getNutritionSummary(startDate, endDate) {
  return apiFetch(`/meals/analytics/summary?start_date=${startDate}&end_date=${endDate}`);
}

export async function getCaloriesConsumed(startDate, endDate) {
  return apiFetch(`/meals/analytics/calories-consumed?start_date=${startDate}&end_date=${endDate}`);
}