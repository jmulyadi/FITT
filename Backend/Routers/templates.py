from fastapi import APIRouter, Depends, HTTPException, status
from dependencies import get_backend
from DBhelpermethods import FitnessBackend
from pydantic import BaseModel
from typing import List, Optional
import json

router = APIRouter()


class TemplateExerciseSet(BaseModel):
    weight: str = ""
    reps: str = ""
    rpe: str = ""


class TemplateExercise(BaseModel):
    name: str
    muscleGroup: str = ""
    muscles: List[str] = []
    sets: List[TemplateExerciseSet] = []


class TemplateCreate(BaseModel):
    name: str
    exercises: List[TemplateExercise]


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    exercises: Optional[List[TemplateExercise]] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_template(user_id: str, body: TemplateCreate, backend: FitnessBackend = Depends(get_backend)):
    """Save current workout as a named template."""
    try:
        uid = backend.get_user_id_from_session()
        response = backend.supabase.table("workout_template").insert({
            "user_id": uid,
            "name": body.name,
            "exercises": [e.model_dump() for e in body.exercises], # Send as a list
        }).execute()
        if not response.data:
            raise RuntimeError("Failed to create template.")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def get_templates(user_id: str, backend: FitnessBackend = Depends(get_backend)):
    """Get all templates for the current user."""
    try:
        uid = backend.get_user_id_from_session()
        response = backend.supabase.table("workout_template") \
            .select("*") \
            .eq("user_id", uid) \
            .order("created_at", desc=True) \
            .execute()
        templates = response.data or []
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}")
def get_template(user_id: str, template_id: str, backend: FitnessBackend = Depends(get_backend)):
    """Get a single template by ID."""
    try:
        response = backend.supabase.table("workout_template") \
            .select("*") \
            .eq("id", template_id) \
            .single() \
            .execute()
        if not response.data:
            raise ValueError("Template not found.")
        t = response.data
        return t
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{template_id}")
def update_template(user_id: str, template_id: str, body: TemplateUpdate, backend: FitnessBackend = Depends(get_backend)):
    """Update a template's name or exercises."""
    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.exercises is not None:
        updates["exercises"] = json.dumps([e.model_dump() for e in body.exercises])
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided.")
    try:
        response = backend.supabase.table("workout_template") \
            .update(updates) \
            .eq("id", template_id) \
            .execute()
        if not response.data:
            raise ValueError("Template not found.")
        t = response.data[0]
        return t
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(user_id: str, template_id: str, backend: FitnessBackend = Depends(get_backend)):
    """Delete a template."""
    try:
        backend.supabase.table("workout_template").delete().eq("id", template_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
