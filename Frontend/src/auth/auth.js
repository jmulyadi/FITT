import { supabase } from "./supabase";

export async function login(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) throw error;

  const token = data.session.access_token;

  localStorage.setItem("access_token", token);

  return data.session;
}

export async function logout() {
  await supabase.auth.signOut();
  localStorage.removeItem("access_token");
}

export function getToken() {
  return localStorage.getItem("access_token");
}
