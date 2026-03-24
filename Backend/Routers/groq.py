from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from groq import Groq
from pydantic import BaseModel
from dependencies import get_backend
from DBhelpermethods import FitnessBackend
from datetime import datetime, timedelta
import os

router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class Message(BaseModel):
    role: str      # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: list[Message]

@router.post("/transcribe", tags=["Groq"])
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio to text using Groq Whisper
    Frontend records audio, sends it here, and gets a text back,
    which is passed as a user message to /groq/chat endpoint for processing.
    Supported formats: .wav, .mp3, .mp4, .mpeg, .m4a, .mpga, .webm.
    """
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API key is not configured")
    try:
        client = Groq(api_key=GROQ_API_KEY)
        # Read file content
        audio_bytes = await file.read()
        # Create transcription
        transcription = client.audio.transcriptions.create(
            file=(file.filename, audio_bytes, file.content_type),
            model="whisper-large-v3", # Free tier model on Groq
            language="en",
            response_format="text"
        )
        return {"transcription": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during transcription: {str(e)}")

def build_user_context(user_profile: dict, workouts: list, meals: list) -> str:
    """
    Builds a formatted context string from user profile and fitness data.
    
    Args:
        user_profile: User profile data from database
        workouts: List of recent workouts
        meals: List of recent meals
        
    Returns:
        Formatted context string for the LLM system prompt
    """
    context = f"""**User Stats:**
- Age: {user_profile['age']}, Gender: {user_profile['gender']}
- Height: {user_profile['height']}cm, Weight: {user_profile['weight']}kg
- BMI: {user_profile['bmi']:.1f}
- Experience Level: {user_profile['experience_level']}

**Recent Workouts (Last 7 Days):**
"""
    
    if workouts:
        total_calories = sum(w['calories_burned'] for w in workouts)
        total_duration = sum(w['duration'] for w in workouts)
        context += f"- Total: {len(workouts)} workouts, {total_duration} mins, {total_calories} calories\n"
        
        # Track muscle groups for summary
        muscle_groups_by_date = {}
        overall_muscle_count = {}
        
        for w in workouts[-3:]:  # Last 3 workouts for detailed overview
            context += f"  • {w['date']}: {w['type'].capitalize()} ({w['duration']}m, {w['calories_burned']}cal)"
            
            if w['type'] == 'cardio' and w.get('cardio_type'):
                context += f" - {w['cardio_type']}"
                if w.get('distance'):
                    context += f" ({w['distance']}km)"
            elif w['type'] == 'strength' and w.get('exercise'):
                # Extract muscle groups from exercises
                muscles = []
                for exercise in w['exercise']:
                    if exercise.get('muscle_group'):
                        muscles.append(exercise['muscle_group'])
                if muscles:
                    context += f" - Muscles: {', '.join(set(muscles))}"
                    muscle_groups_by_date[w['date']] = set(muscles)
            
            context += "\n"
        
        # Calculate overall muscle group frequency across all strength workouts
        for workout in workouts:
            if workout['type'] == 'strength' and workout.get('exercise'):
                for exercise in workout['exercise']:
                    if exercise.get('muscle_group'):
                        muscle = exercise['muscle_group']
                        overall_muscle_count[muscle] = overall_muscle_count.get(muscle, 0) + 1
        
        # Add muscle group summary
        if overall_muscle_count:
            context += f"\n**Muscle Group Summary (Last 7 Days):**\n"
            sorted_muscles = sorted(overall_muscle_count.items(), key=lambda x: x[1], reverse=True)
            for muscle, count in sorted_muscles:
                context += f"  • {muscle}: {count} session(s)\n"
            
            # Identify muscle imbalances
            if len(sorted_muscles) > 1:
                most_worked = sorted_muscles[0][1]
                least_worked = sorted_muscles[-1][1]
                if most_worked > least_worked * 1.5:  # 50% more volume
                    context += f"  ⚠️  Note: {sorted_muscles[0][0]} has significantly more volume than {sorted_muscles[-1][0]}. Consider balancing.\n"
    else:
        context += "- No recent workouts\n"

    context += f"\n**Recent Nutrition (Last 7 Days):**\n"
    if meals:
        total_calories_in = sum(m['calories_in'] for m in meals)
        unique_dates = set(m['date'] for m in meals)
        avg_per_day = total_calories_in / max(len(unique_dates), 1)
        context += f"- Total calories: {total_calories_in}, Avg/day: {avg_per_day:.0f}\n"
        # Group by date (show last 3 days)
        by_date = {}
        for m in meals:
            if m['date'] not in by_date:
                by_date[m['date']] = 0
            by_date[m['date']] += m['calories_in']
        for date in sorted(by_date.keys(), reverse=True)[:3]:
            context += f"  • {date}: {by_date[date]} calories\n"
    else:
        context += "- No recent meals logged\n"
    
    return context


@router.post("/chat", tags=["Groq"])
async def groq_chat(
    request: ChatRequest,
    backend: FitnessBackend = Depends(get_backend)
):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API key is not configured")

    try:
        # Get user information for context
        username = backend.get_username_from_session()
        user_profile = backend.get_user(username)
        
        # Calculate date range (last 7 days)
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=7)
        
        # Fetch recent data
        recent_workouts = backend.get_workouts_in_range(
            username,
            start_date=seven_days_ago.isoformat(),
            end_date=today.isoformat()
        )
        
        recent_meals = backend.get_meals_in_range(
            username,
            start_date=seven_days_ago.isoformat(),
            end_date=today.isoformat()
        )
        
        # Build context string
        user_context = build_user_context(user_profile, recent_workouts, recent_meals)
        
        # Create enhanced system prompt with user context
        system_prompt = f"""You are FITT, a helpful fitness and nutrition assistant. Help users with workout plans, exercise advice, and meal guidance.

Use the following user data to provide personalized, contextual, and concise recommendations:

{user_context}

Based on this user's profile and recent activity, provide tailored advice that considers their fitness level, recent workouts, nutrition patterns, and personal goals."""

        client = Groq(api_key=GROQ_API_KEY)

        # Prepend the system prompt, then append the conversation history
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + [{"role": m.role, "content": m.content} for m in request.messages]

        chat_completion = client.chat.completions.create(
            messages=full_messages,
            model="llama-3.3-70b-versatile",
        )

        response_text = chat_completion.choices[0].message.content
        return {"response": response_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interacting with Groq: {str(e)}")