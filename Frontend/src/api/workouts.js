const API_BASE = "http://localhost:8000";

export async function searchExercises(name) {
  const res = await fetch(`${API_BASE}/workouts/exercise-search?name=${name}`);

  if (!res.ok) {
    throw new Error("Failed to search exercises");
  }

  return res.json();
}
