from typing import Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import os


class Authentication:
    def __init__(self):
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_anon_key or not supabase_service_key:
            raise ValueError("SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY must be set in .env")

        # Regular client — used for all normal user operations
        self.supabase: Client = create_client(supabase_url, supabase_anon_key)

        # Admin client — only used for privileged operations 
        self.supabase_admin: Client = create_client(supabase_url, supabase_service_key)

    def sign_up(self, email: str, password: str, username: str, age: int,
                gender: str, weight: float, height: float,
                experience: str, bmi: float) -> Dict[str, Any]:
        """
        Registers a new user with Supabase Auth, then creates their profile.
        """
        auth_response = self.supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if not auth_response.user:
            raise RuntimeError("Sign up failed.")

        user_id = auth_response.user.id

        profile_data = {
            "id": user_id,
            "username": username,
            "age": age,
            "gender": gender,
            "weight": weight,
            "height": height,
            "experience_level": experience,
            "bmi": bmi
        }

        try:
            response = self.supabase.table("USER").insert(profile_data).execute()
            if not response.data:
                raise RuntimeError("Profile insert returned no data.")
        except Exception as e:
            # Roll back the auth account using admin client so we don't leave an orphaned user
            self.supabase_admin.auth.admin.delete_user(user_id)
            raise RuntimeError(f"Sign up failed during profile creation: {e}")

        return {"user_id": user_id, "username": username, "email": email}

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Signs in a user, sets the active session, and returns tokens.
        Call set_session() with the returned tokens to authenticate DB calls.
        """
        auth_response = self.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not auth_response.user:
            raise ValueError("Invalid email or password.")

        # Automatically set the session so DB calls are authenticated immediately
        self.supabase.auth.set_session(
            auth_response.session.access_token,
            auth_response.session.refresh_token
        )

        # Fetch username from USER table — it is not stored in auth metadata
        profile = self.supabase.table("USER") \
            .select("username") \
            .eq("id", auth_response.user.id) \
            .execute()

        username = profile.data[0]["username"] if profile.data else None

        return {
            "user_id": auth_response.user.id,
            "username": username,
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "expires_at": auth_response.session.expires_at
        }

    def set_session(self, access_token: str, refresh_token: str) -> None:
        """
        Restores a session from stored tokens (e.g. on app relaunch).
        """
        self.supabase.auth.set_session(access_token, refresh_token)

    def sign_out(self) -> None:
        """Signs out the current user and invalidates their session."""
        self.supabase.auth.sign_out()

    def get_current_user(self) -> Dict[str, Any]:
        """
        Returns the currently authenticated user.
        """
        user = self.supabase.auth.get_user()

        if not user or not user.user:
            raise PermissionError("No active session. Please sign in.")

        return {"user_id": user.user.id, "email": user.user.email}

    def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refreshes an expired access token.
        """
        response = self.supabase.auth.refresh_session(refresh_token)

        if not response.session:
            raise RuntimeError("Session refresh failed. User must sign in again.")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_at": response.session.expires_at
        }

    def reset_password_request(self, email: str) -> None:
        """Sends a password reset email."""
        self.supabase.auth.reset_password_email(email)

    def delete_account(self, user_id: str) -> None:
        """
        Permanently deletes a user's Supabase Auth account.
        CASCADE on the USER table will automatically delete their profile,
        workouts, meals, and all associated data.
        
        Args:
            user_id: The Supabase auth UUID of the user to delete
        """
        self.supabase_admin.auth.admin.delete_user(user_id)
        
    def get_backend(self):
        """
        Returns a FitnessBackend instance sharing this authenticated session.

        """
        from DBhelpermethods import FitnessBackend
        return FitnessBackend(self.supabase)

    def update_password(self, new_password: str) -> None:
        """Updates password for the currently signed-in user."""
        self.supabase.auth.update_user({"password": new_password})