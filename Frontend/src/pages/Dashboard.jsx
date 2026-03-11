// ─────────────────────────────────────────────────────────────────────────────
// Dashboard.jsx — Live data home screen
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useEffect } from 'react'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  Filler, Tooltip
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import {
  getMyProfile, getWorkoutsInRange, getMealsByDate
} from '../api/dashboard'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip)

// ── date helpers ──────────────────────────────────────────────────────────────
const localDate = (d = new Date()) => {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const mondayOfWeek = () => {
  const d = new Date()
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  return localDate(d)
}

const nDaysAgo = (n) => {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return localDate(d)
}

const fmtDay = () => new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

const epley1RM = (weight, reps) => Math.round(weight * (1 + reps / 30))

const bestRMFromWorkout = (workout, exerciseName) => {
  const exercises = workout.exercise || workout.exercises || []
  let best = 0
  for (const ex of exercises) {
    if (!ex.name?.toLowerCase().includes(exerciseName.toLowerCase())) continue
    const sets = ex.SET || ex.sets || []
    for (const s of sets) {
      if (s.reps && s.weight) {
        const rm = epley1RM(s.weight, s.reps)
        if (rm > best) best = rm
      }
    }
  }
  return best
}

const chartOptions = {
  responsive: true,
  plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `${ctx.parsed.y} lbs` } } },
  scales: {
    x: { grid: { color: '#2a3347' }, ticks: { color: '#8899aa', font: { size: 11 } } },
    y: { grid: { color: '#2a3347' }, ticks: { color: '#8899aa', font: { size: 11 } } }
  }
}

// ── Inline AI insight card (no external component needed) ─────────────────────
function AICard({ children }) {
  return (
    <div className="card fade-in" style={{ borderLeft: '3px solid #3b82f6', marginBottom: 12 }}>
      <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: '#3b82f6', marginBottom: 6 }}>
        AI Insight
      </div>
      <div style={{ fontSize: 14, color: 'var(--text)', lineHeight: 1.6 }}>{children}</div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function Dashboard({ goTo }) {
  const [profile, setProfile]           = useState(null)
  const [weekWorkouts, setWeekWorkouts] = useState([])
  const [calories, setCalories]         = useState(null)
  const [rmData, setRmData]             = useState([])
  const [topExercise, setTopExercise]   = useState(null)
  const [weekSummary, setWeekSummary]   = useState(null)
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState(null)

  useEffect(() => {
    const today   = localDate()
    const monday  = mondayOfWeek()
    const monthAgo = nDaysAgo(28)

    Promise.allSettled([
      getMyProfile(),
      getWorkoutsInRange(monday, today),
      getMealsByDate(today),
      getWorkoutsInRange(monthAgo, today),
    ]).then(([profRes, weekRes, mealsRes, monthRes]) => {
      try {
        if (profRes.status === 'fulfilled') setProfile(profRes.value)

        const wks = weekRes.status === 'fulfilled' && Array.isArray(weekRes.value) ? weekRes.value : []
        setWeekWorkouts(wks)

        if (mealsRes.status === 'fulfilled') {
          const meals = Array.isArray(mealsRes.value) ? mealsRes.value : []
          const totalIn = meals.reduce((s, m) => s + (m.calories_in || 0), 0)
          setCalories({ calories_in: totalIn, calories_burned: 0, net_calories: totalIn })
        }

        const cardio    = wks.filter(w => w.type === 'cardio').length
        const strength  = wks.filter(w => w.type === 'strength').length
        const totalDur  = wks.reduce((s, w) => s + (w.duration || 0), 0)
        setWeekSummary({ cardio_sessions: cardio, strength_sessions: strength, total_duration: totalDur })

        const all = monthRes.status === 'fulfilled' && Array.isArray(monthRes.value) ? monthRes.value : []
        const nameCounts = {}
        for (const w of all) {
          for (const ex of (w.exercise || w.exercises || [])) {
            if (ex.name) nameCounts[ex.name] = (nameCounts[ex.name] || 0) + 1
          }
        }
        const topName = Object.entries(nameCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || null
        setTopExercise(topName)

        if (topName) {
          const points = all
            .map(w => ({ date: w.date, rm: bestRMFromWorkout(w, topName) }))
            .filter(p => p.rm > 0)
            .sort((a, b) => a.date.localeCompare(b.date))
          setRmData(points)
        }
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    })
  }, [])

  const username      = profile?.username || 'there'
  const WORKOUTS_GOAL = 5
  const workoutsDone  = weekWorkouts.length
  const circum        = 2 * Math.PI * 32
  const ringOffset    = circum * (1 - Math.min(workoutsDone / WORKOUTS_GOAL, 1))
  const calIn         = calories?.calories_in    ?? 0
  const calBurned     = calories?.calories_burned ?? 0
  const calGoal       = 2400

  const weeklyVolume = weekWorkouts.reduce((total, w) => {
    return total + (w.exercise || w.exercises || []).reduce((t2, ex) => {
      return t2 + (ex.SET || ex.sets || []).reduce((t3, s) => t3 + (s.weight || 0) * (s.reps || 0), 0)
    }, 0)
  }, 0)
  const volumeDisplay = weeklyVolume >= 1000
    ? `${(weeklyVolume / 1000).toFixed(1)}k` : Math.round(weeklyVolume).toString()

  const latestRM = rmData.length > 0 ? rmData[rmData.length - 1].rm : null

  const chartData = {
    labels: rmData.map(p => { const [,m,d] = p.date.split('-'); return `${parseInt(m)}/${parseInt(d)}` }),
    datasets: [{
      data: rmData.map(p => p.rm),
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.12)',
      tension: 0.4,
      pointBackgroundColor: '#3b82f6',
      fill: true,
    }]
  }

  const recoveryScore = weekSummary
    ? Math.min(100, Math.round(
        50
        + (workoutsDone >= 3 ? 20 : workoutsDone * 7)
        + (calIn >= 1800 ? 15 : Math.round(calIn / 120))
        + (weekSummary.total_duration ? Math.min(15, Math.round(weekSummary.total_duration / 20)) : 0)
      ))
    : null

  const recoveryColor = recoveryScore == null ? '#8899aa'
    : recoveryScore >= 75 ? '#22c55e'
    : recoveryScore >= 50 ? '#f59e0b' : '#ef4444'
  const recoveryLabel = recoveryScore == null ? '—'
    : recoveryScore >= 75 ? 'Green Light' : recoveryScore >= 50 ? 'Take It Easy' : 'Rest Day'

  const aiInsight = (() => {
    if (loading) return 'Loading your data...'
    const parts = []
    if (latestRM && topExercise) parts.push(`Your ${topExercise} 1RM estimate is ${latestRM} lbs.`)
    if (workoutsDone === 0) parts.push("No workouts logged this week yet — let's get moving.")
    else if (workoutsDone >= WORKOUTS_GOAL) parts.push(`You've hit your ${WORKOUTS_GOAL}-workout goal this week!`)
    else parts.push(`${workoutsDone} of ${WORKOUTS_GOAL} workouts done this week — keep it up.`)
    if (calIn > 0) parts.push(`You're at ${Math.round((calIn / calGoal) * 100)}% of your calorie goal today.`)
    if (recoveryScore != null) parts.push(`Recovery score: ${recoveryScore}/100 — ${recoveryLabel}.`)
    return parts.join(' ') || 'Log a workout or meal to see your personalized insights.'
  })()

  if (error) return (
    <div className="page" style={{ padding: 32, color: '#ef4444' }}>
      Dashboard error: {error}
    </div>
  )

  return (
    <div className="page fade-in">

      {/* Hero */}
      <div className="dash-hero">
        <div className="dash-greeting">{fmtDay()}</div>
        <div className="dash-name">Hey, {username}</div>
        <div className="recovery-pill" style={{ borderColor: recoveryColor + '55', background: recoveryColor + '18' }}>
          <div className="pulse" style={{ background: recoveryColor }} />
          {recoveryScore != null
            ? `Recovery Score: ${recoveryScore}/100 · ${recoveryLabel}`
            : 'Calculating recovery...'}
        </div>
      </div>

      <div className="page-content">
        <div style={{ height: 14 }} />

        <AICard>{aiInsight}</AICard>

        {/* Weekly ring */}
        <div className="card fade-in">
          <div className="card-title">This Week</div>
          <div className="ring-row">
            <div className="ring-wrap">
              <svg width="80" height="80" viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="32" fill="none" stroke="#2a3347" strokeWidth="8"/>
                <circle cx="40" cy="40" r="32" fill="none" stroke="#3b82f6" strokeWidth="8"
                  strokeDasharray={circum} strokeDashoffset={ringOffset}
                  strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.6s ease' }}/>
              </svg>
              <div className="ring-center">{workoutsDone}<span>/ {WORKOUTS_GOAL}</span></div>
            </div>
            <div className="ring-info">
              <h3>{workoutsDone} of {WORKOUTS_GOAL} Workouts Done</h3>
              {weekSummary && (
                <p>
                  {weekSummary.cardio_sessions > 0 && <>{weekSummary.cardio_sessions} cardio · </>}
                  {weekSummary.strength_sessions > 0 && <>{weekSummary.strength_sessions} strength · </>}
                  {weekSummary.total_duration > 0 && <>{Math.round(weekSummary.total_duration / (workoutsDone || 1))} min avg</>}
                </p>
              )}
              {!weekSummary && !loading && <p style={{ color: 'var(--muted)', fontSize: 13 }}>No workouts yet this week</p>}
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div className="stat-row">
          <div className="stat-card">
            <div className="stat-label">Weekly Volume</div>
            <div className="stat-val blue">{weeklyVolume > 0 ? volumeDisplay : '—'}</div>
            <div className="stat-sub">{weeklyVolume > 0 ? 'lbs this week' : 'no sets logged'}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">{topExercise ? `${topExercise} 1RM` : 'Top Lift'}</div>
            <div className="stat-val green">{latestRM ?? '—'}</div>
            <div className="stat-sub">{latestRM ? 'lbs est.' : 'no data yet'}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Calories Today</div>
            <div className="stat-val orange">{calIn > 0 ? calIn.toLocaleString() : '—'}</div>
            <div className="stat-sub">/ {calGoal.toLocaleString()} goal{calBurned > 0 ? ` · -${calBurned} burned` : ''}</div>
          </div>
        </div>

        {/* 1RM trend chart */}
        <div className="card fade-in">
          <div className="card-title">
            {topExercise ? `${topExercise} 1RM – 4 Weeks` : '1RM Trend – 4 Weeks'}
          </div>
          {rmData.length >= 2 ? (
            <Line data={chartData} options={chartOptions} height={120} />
          ) : (
            <div style={{ color: 'var(--muted)', fontSize: 13, padding: '16px 0', textAlign: 'center' }}>
              {loading ? 'Loading...' : 'Log at least 2 sessions with the same exercise to see your trend.'}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div style={{ padding: '0 16px', marginBottom: 14, fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--muted)' }}>
          Quick Actions
        </div>
        <div className="quick-actions">
          <div className="qa-btn" onClick={() => goTo('workout')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6.5 6.5h11M6.5 17.5h11M3 12h18M6 8.5v7M18 8.5v7"/>
            </svg>
            <span>Workout</span>
          </div>
          <div className="qa-btn" onClick={() => goTo('nutrition')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/>
            </svg>
            <span>Log Meal</span>
          </div>
          <div className="qa-btn" onClick={() => goTo('recovery')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
            <span>Recovery</span>
          </div>
          <div className="qa-btn" onClick={() => goTo('chat')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span>Ask AI</span>
          </div>
        </div>

      </div>
    </div>
  )
}