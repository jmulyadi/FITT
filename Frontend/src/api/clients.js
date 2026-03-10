import { getToken } from "../auth/auth";
import { API_BASE } from "../config";

export async function apiFetch(path, options = {}) {
  const token = getToken();

  const res = await fetch(`${API_BASE}${path}`, {
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

  // 204 No Content has no body — don't try to parse JSON
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return null;
  }

  return res.json();
}