// ─────────────────────────────────────────────────────────────────────────────
// mockData.js — All static/placeholder data for the frontend
//
// IMPORTANT: Everything in this file is hardcoded mock data used while the
// backend is not yet connected. When backend integration begins, each export
// here should be replaced with real API calls (fetch / axios).
//
// Also contains shared Chart.js config (chartDefaults) used across all pages.
// ─────────────────────────────────────────────────────────────────────────────


// ── Shared Chart.js options ───────────────────────────────────────────────────
// Applied to every chart in the app to keep the dark theme consistent.
// Pages can spread this and override individual properties as needed.
export const chartDefaults = {
  responsive: true,
  plugins: { legend: { display: false } },   // hide the legend on all charts
  scales: {
    x: { grid: { color: '#2a3347' }, ticks: { color: '#64748b', font: { size: 10 } } },
    y: { grid: { color: '#2a3347' }, ticks: { color: '#64748b', font: { size: 10 } } },
  },
}


// ── Dashboard — Squat 1RM trend (Line chart, 4 weeks) ────────────────────────
// TODO: Replace with GET /analytics/exercises/progress/squat
export const dashChartData = {
  labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
  datasets: [{
    data: [245, 255, 262, 275],
    borderColor: '#3b82f6',
    backgroundColor: 'rgba(59,130,246,.1)',  // light blue fill under line
    pointBackgroundColor: '#3b82f6',
    fill: true, tension: 0.4, pointRadius: 5,
  }],
}


// ── Recovery — 7-day sleep history (Bar chart) ───────────────────────────────
// Bar color changes based on sleep quality: green ≥7h, orange ≥6h, red <6h
// TODO: Replace with GET /recovery/sleep-log
export const sleepChartData = {
  labels: ['Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon', 'Tue'],
  datasets: [{
    data: [7.2, 6.5, 5.8, 8.1, 7.5, 5.2, 4.8],
    // Chart.js calls this function per bar to determine its color
    backgroundColor: (ctx) => {
      const v = ctx.dataset.data[ctx.dataIndex]
      return v >= 7 ? 'rgba(34,197,94,.7)' : v >= 6 ? 'rgba(245,158,11,.7)' : 'rgba(239,68,68,.7)'
    },
    borderRadius: 6,
  }],
}


// ── Progress — Weekly total volume (Bar chart, 8 weeks) ──────────────────────
// TODO: Replace with GET /analytics/workouts/summary
export const volumeChartData = {
  labels: ['Wk 1', 'Wk 2', 'Wk 3', 'Wk 4', 'Wk 5', 'Wk 6', 'Wk 7', 'Wk 8'],
  datasets: [{
    data: [32000, 35500, 33000, 38000, 40000, 37500, 41000, 42500],
    backgroundColor: 'rgba(59,130,246,.65)',
    borderRadius: 6,
  }],
}


// ── Progress — Estimated 1RM data per lift (Line chart, 8 weeks) ─────────────
// Each key maps to a lift name. The Progress page uses `activeLift` state to
// pick which entry to display. Each lift has a unique accent color.
// TODO: Replace with GET /analytics/exercises/progress/{name}
export const liftData = {
  squat:    { label: 'Squat – Estimated 1RM',    data: [225,235,242,250,255,262,268,275], color: '#3b82f6' },
  bench:    { label: 'Bench – Estimated 1RM',    data: [195,200,205,205,210,215,220,225], color: '#22d3ee' },
  deadlift: { label: 'Deadlift – Estimated 1RM', data: [295,310,320,330,335,345,355,365], color: '#22c55e' },
  ohp:      { label: 'OHP – Estimated 1RM',      data: [115,120,125,125,130,135,138,145], color: '#f59e0b' },
}

// Shared x-axis labels for any 8-week chart
export const weeks8 = ['Wk 1', 'Wk 2', 'Wk 3', 'Wk 4', 'Wk 5', 'Wk 6', 'Wk 7', 'Wk 8']


// ── Progress — Personal records list ─────────────────────────────────────────
// TODO: Replace by deriving max weight per exercise from the sets data
export const prData = [
  { trophy: '🏆', lift: 'Back Squat',     weight: '275 lbs', date: 'Feb 22' },
  { trophy: '🥈', lift: 'Bench Press',    weight: '225 lbs', date: 'Feb 18' },
  { trophy: '🥈', lift: 'Deadlift',       weight: '365 lbs', date: 'Feb 10' },
  { trophy: '🥉', lift: 'Overhead Press', weight: '145 lbs', date: 'Jan 28' },
]


// ── Nutrition — Today's meal log ──────────────────────────────────────────────
// `cal: null` means the meal hasn't been logged yet (renders as "—")
// TODO: Replace with GET /meals?date=today
export const mealsData = [
  { icon: '🌅', bg: 'rgba(251,191,36,.12)', name: 'Breakfast',          sub: 'Greek Yogurt · Oats · Blueberries',   cal: '520 cal' },
  { icon: '☀️', bg: 'rgba(34,197,94,.12)',  name: 'Lunch',              sub: 'Chicken Rice Bowl · Broccoli',        cal: '680 cal' },
  { icon: '🥤', bg: 'rgba(59,130,246,.12)', name: 'Post-Workout Shake', sub: 'Whey Protein · Banana · Almond Milk', cal: '380 cal' },
  { icon: '🌙', bg: 'rgba(148,163,184,.1)', name: 'Dinner',             sub: 'Not logged yet',                      cal: null },
]


// ── Workout — Exercise list for today's session ───────────────────────────────
// Each exercise has a name, target muscle groups, a list of sets (weight/reps/rpe),
// and a `prev` string showing last session's performance for comparison.
// Sets with empty weight/reps are treated as "not yet completed" in the UI.
// TODO: Replace with GET /workouts/{workout_id} which nests exercises and sets
export const initialExercises = [
  {
    name: 'Bench Press',
    muscles: ['Chest', 'Triceps'],
    sets: [
      { weight: '185', reps: '8', rpe: '7' },  // completed sets have values pre-filled
      { weight: '185', reps: '7', rpe: '8' },
      { weight: '185', reps: '',  rpe: ''  },  // empty = set not yet done
    ],
    prev: 'Last session: 3×8 @ 180 lbs · Volume: 4,320 lbs',
  },
  {
    name: 'Overhead Press',
    muscles: ['Shoulders'],
    sets: [
      { weight: '115', reps: '8', rpe: '6' },
      { weight: '115', reps: '8', rpe: '7' },
      { weight: '',    reps: '',  rpe: ''  },
    ],
    prev: 'Last session: 3×8 @ 110 lbs',
  },
  {
    name: 'Tricep Pushdown',
    muscles: ['Triceps'],
    sets: [
      { weight: '50', reps: '12', rpe: '6' },
      { weight: '',   reps: '',   rpe: ''  },
    ],
    prev: 'Last session: 2×12 @ 45 lbs',
  },
]


// ── AI Chat — Keyword-matched responses ──────────────────────────────────────
// The Chat page scans the user's message for these keys (lowercase).
// If a key is found anywhere in the message, the matching response is returned.
// This is placeholder logic — real implementation should call POST /ai/chat (Groq).
export const aiResponses = {
  'bench':   "Looking at your last 3 sessions: bench volume dropped 11% and your RPE jumped from 7 to 9. Combined with your 4.8hr sleep log from Monday, this is a classic overtraining + sleep deficit pattern. Recommend keeping bench at 185 lbs for 1–2 more sessions before progressing.",
  'deload':  "Based on your data: recovery score is 42/100, sleep averaged 5.4 hrs this week, and your RPE has been consistently high (8–9). Yes — a deload is warranted. I recommend 50–60% of normal volume for the next 5 days, then reassess.",
  'protein': "Your goal is 180g protein. You've logged 142g so far today. With the high-intensity session you did, I'm bumping your target to 200g. You need about 58g more — that's roughly a chicken breast + protein shake.",
  'eat':     "Post your upper-body session: aim for 40g protein + 60–80g fast carbs within 45 minutes. Ideal options: whey shake + banana + rice cakes, or chicken + white rice. Your glycogen stores are depleted — don't skip this window.",
}

// Fallback response when no keyword matches
export const defaultAIResponse = "I've analyzed your recent data. Your training is trending in the right direction — squat 1RM is up 15 lbs in 3 weeks. The main area to watch is sleep quality; it's directly correlated with your performance drops. Want me to drill into any specific lift, meal, or recovery metric?"

// Quick-tap suggestion chips shown above the chat input
export const suggestedChips = [
  'Why did my bench drop?',
  'Should I deload?',
  'How much protein today?',
  'What should I eat post-workout?',
]
