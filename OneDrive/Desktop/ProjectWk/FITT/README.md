# Team

Developed by:

Josh Mulyadi

Sohom Dey

Steven Zhang

Sania Mathew

Felix Bogart

Massimo Adams

The Ohio State University
CSE Knowledge-Based Systems Project

---

# FITT 💪

### How to Run

Make sure to have docker installed
run

```bash

docker compose up --build
```

If image has been built already don't need --build

```bash

docker compose up
```

### AI-Powered Fitness & Wellness Coach

**FITT** is an AI-powered coaching platform designed to help users improve their **fitness, nutrition, sleep, and overall wellness**.

Instead of just tracking health data, FITT analyzes workout performance and recovery signals to provide **personalized recommendations** that help users train smarter, recover better, and build healthier habits.

---

# 🚀 Features

- **AI Fitness Coaching**
  Analyze workout performance and suggest progression, deloads, and training adjustments.

- **Nutrition Guidance**
  Provide calorie and macronutrient recommendations based on activity levels.

- **Recovery Insights**
  Adjust training recommendations based on sleep and fatigue signals.

- **Conversational AI Coach**
  Users can ask questions like:

  - _“What should I eat after my workout?”_
  - _“Why did my strength drop today?”_

- **Performance Tracking**
  Track workouts, nutrition, and progress over time.

---

# 🏗 Architecture

```text
User
  │
  ▼
Frontend (React) – Vercel
  │
  ▼
Backend (FastAPI)
  │
  ├── Supabase (Database & Auth)
  └── Groq AI (LLM recommendations)
```

---

# 🛠 Tech Stack

**Frontend**

- React
- Vercel

**Backend**

- FastAPI
- Python

**AI**

- Groq AI

**Database**

- Supabase (PostgreSQL)

**APIs / Data**

- ExerciseDB
- Open Food Facts
- Fitness datasets

---

# ⚙️ Setup

Setup instructions will be added soon.

This section will include:

- Installing dependencies
- Configuring environment variables
- Connecting Supabase
- Setting up Groq API keys
- Running the backend and frontend locally

Example `.env` file:

```bash
SUPABASE_URL=
SUPABASE_KEY=
GROQ_API_KEY=
DATABASE_URL=
```

## Production Deploy

The cleanest setup for this repo is:

- Deploy `Frontend/` to Vercel as a Vite project
- Deploy `Backend/` to Vercel as a separate FastAPI project
- Keep Supabase and Groq as managed external services

### Frontend on Vercel

Set the Vercel project root directory to `Frontend`.

Add these environment variables in Vercel:

```bash
VITE_API_BASE=https://your-backend-project.vercel.app
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

Build settings:

- Build command: `npm run build`
- Output directory: `dist`

### Backend on Vercel

Set the Vercel project root directory to `Backend`.

Add these environment variables in Vercel:

```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-key
EXERCISEDB_API_KEY=your-rapidapi-key
EXERCISEDB_API_HOST=exercisedb.p.rapidapi.com
EXERCISEDB_BASE_URL=https://exercisedb.p.rapidapi.com
CORS_ORIGINS=https://your-frontend-project.vercel.app
```

If you use a custom frontend domain, include that in `CORS_ORIGINS` too. For multiple origins, use a comma-separated list.

---

Developed by students at **The Ohio State University**.

---
