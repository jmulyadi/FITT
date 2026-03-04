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

---

# 👨‍💻 Team

Developed by students at **The Ohio State University**.

---
