import { API_BASE } from "../config";

function getToken() {
  return localStorage.getItem("access_token");
}

function getUserId() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return payload.sub;
  } catch {
    return null;
  }
}

export async function apiFetch(path, options = {}) {
  const token = getToken();
  const userId = getUserId();

  // Inject user_id into paths that need it
  const fullPath = path.startsWith("/workouts") || path.startsWith("/meals") || path.startsWith("/groq")
    ? `/users/${userId}${path}`
    : path;

  const res = await fetch(`${API_BASE}${fullPath}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }

  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return null;
  }

  return res.json();
}