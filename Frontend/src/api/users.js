import { API_BASE } from "../config";

export async function createUser(userData) {
  console.log("Signup payload:", userData);
  const res = await fetch(`${API_BASE}/users/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(userData),
  });
  console.log("JSON being sent:", JSON.stringify(userData));
  if (!res.ok) {
    throw new Error("Signup failed");
  }

  return res.json();
}
