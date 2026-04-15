import { apiFetch } from "./clients";

// ── Workouts ──────────────────────────────────────────────────────────────────

export async function createWorkout(data) {
  // data: { date, duration, calories_burned, type, cardio_type?, distance? }
  return apiFetch("/workouts/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getWorkouts(startDate, endDate) {
  let path = "/workouts/";
  const params = new URLSearchParams();
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);
  if ([...params].length) path += "?" + params.toString();
  return apiFetch(path);
}

// ── Exercises ─────────────────────────────────────────────────────────────────

export async function addExercise(workoutId, name, muscleGroup) {
  return apiFetch(`/workouts/${workoutId}/exercises`, {
    method: "POST",
    body: JSON.stringify({ name, muscle_group: muscleGroup }),
  });
}

// ── Sets ──────────────────────────────────────────────────────────────────────

export async function addSet(workoutId, exerciseId, setNum, reps, weight, intensity) {
  return apiFetch(`/workouts/${workoutId}/exercises/${exerciseId}/sets`, {
    method: "POST",
    body: JSON.stringify({
      set_num: setNum,
      reps,
      weight,
      intensity,
    }),
  });
}

// ── Exercise Search (ExerciseDB) ──────────────────────────────────────────────

export async function searchExercises(name, limit = 10) {
  return apiFetch(`/workouts/exercise-search?name=${encodeURIComponent(name)}&limit=${limit}`);
}

// ── Delete Workout ─────────────────────────────────────────────────────────────

export async function deleteWorkout(workoutId) {
  return apiFetch(`/workouts/${workoutId}`, { method: "DELETE" });
}