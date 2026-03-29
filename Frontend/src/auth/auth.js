import { supabase } from "./supabase";
import { API_BASE } from "../config";

export async function login(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) throw error;

  const token = data.session.access_token;
  localStorage.setItem("access_token", token);

  // Fetch username from backend using the user's UUID
  try {
    const res = await fetch(`${API_BASE}/users/${data.user.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const profile = await res.json();
      if (profile.username) {
        localStorage.setItem("username", profile.username);
      }
    }
  } catch {}

  return data.session;
}

export async function logout() {
  await supabase.auth.signOut();
  localStorage.removeItem("access_token");
  localStorage.removeItem("username");
}

export function getToken() {
  return localStorage.getItem("access_token");
}

export function getUsername() {
  return localStorage.getItem("username");
}