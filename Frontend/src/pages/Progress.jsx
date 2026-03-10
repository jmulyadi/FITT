// ─────────────────────────────────────────────────────────────────────────────
// Progress.jsx — Live stats derived from real workout history
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useMemo } from 'react'
import { Line, Bar } from 'react-chartjs-2'
import AICard from '../components/AICard'
import { chartDefaults } from '../data/mockData'
import { getWorkouts, deleteWorkout } from '../api/workouts'

// ── Helpers ───────────────────────────────────────────────────────────────────

// Epley 1RM formula: weight × (1 + reps/30)
const epley1RM = (weight, reps) => reps === 1 ? weight : weight * (1 + reps / 30)

// Monday of the week containing a date string
function weekStart(dateStr) {
  const d = new Date(dateStr)
  const day = d.getDay() // 0=Sun
  const diff = (day === 0 ? -6 : 1 - day)
  d.setDate(d.getDate() + diff)
  return d.toISOString().split('T')[0]
}

function fmt(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const LIFT_COLORS = {
  squat:     '#3b82f6',
  bench:     '#22c55e',
  deadlift:  '#f59e0b',
  ohp:       '#a855f7',
}

const volumeOptions = {
  ...chartDefaults,
  scales: {
    ...chartDefaults.scales,
    y: {
      ...chartDefaults.scales.y,
      ticks: {
        ...chartDefaults.scales.y.ticks,
        callback: v => v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v,
      },
    },
  },
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Progress() {
  const [history, setHistory]           = useState([])
  const [loading, setLoading]           = useState(true)
  const [expandedId, setExpandedId]     = useState(null)
  const [deletingId, setDeletingId]     = useState(null)
  const [activeLift, setActiveLift]     = useState(null) // set after data loads

  useEffect(() => {
    getWorkouts()
      .then(data => {
        const sorted = (Array.isArray(data) ? data : [])
          .sort((a, b) => a.date.localeCompare(b.date))
        setHistory(sorted)
      })
      .catch(err => console.error('Failed to load workouts', err))
      .finally(() => setLoading(false))
  }, [])

  // ── Derived stats ──────────────────────────────────────────────────────────

  const stats = useMemo(() => {
    if (!history.length) return null

    // All sets across all workouts
    const allSets = []
    for (const w of history) {
      for (const ex of (w.exercise || [])) {
        for (const s of (ex.SET || [])) {
          allSets.push({ ...s, exerciseName: ex.name.toLowerCase(), date: w.date })
        }
      }
    }

    // PRs: max weight per exercise
    const prMap = {}
    for (const s of allSets) {
      const key = s.exerciseName
      if (!prMap[key] || s.weight > prMap[key].weight) {
        prMap[key] = { weight: s.weight, date: s.date, reps: s.reps }
      }
    }
    const prs = Object.entries(prMap)
      .sort((a, b) => b[1].weight - a[1].weight)
      .slice(0, 6)

    // Detected lifts (exercises with data)
    const liftNames = Object.keys(prMap)

    // Weekly volume: sum weight*reps per week
    const weekMap = {}
    for (const w of history) {
      const wk = weekStart(w.date)
      if (!weekMap[wk]) weekMap[wk] = 0
      for (const ex of (w.exercise || [])) {
        for (const s of (ex.SET || [])) {
          weekMap[wk] += s.weight * s.reps
        }
      }
    }
    const weekLabels = Object.keys(weekMap).sort().slice(-8)
    const weekVolumes = weekLabels.map(wk => Math.round(weekMap[wk]))

    // 1RM progression per exercise: max estimated 1RM per week
    const orm1Map = {} // { exerciseName: { weekStart: max1RM } }
    for (const s of allSets) {
      const wk = weekStart(s.date)
      if (!orm1Map[s.exerciseName]) orm1Map[s.exerciseName] = {}
      const est = epley1RM(s.weight, s.reps)
      if (!orm1Map[s.exerciseName][wk] || est > orm1Map[s.exerciseName][wk]) {
        orm1Map[s.exerciseName][wk] = Math.round(est)
      }
    }

    // This week stats
    const thisWeek = weekStart(new Date().toISOString().split('T')[0])
    const lastWeek = (() => {
      const d = new Date(thisWeek)
      d.setDate(d.getDate() - 7)
      return d.toISOString().split('T')[0]
    })()
    const thisWeekWorkouts = history.filter(w => weekStart(w.date) === thisWeek)
    const lastWeekWorkouts = history.filter(w => weekStart(w.date) === lastWeek)
    const thisWeekVol = weekMap[thisWeek] || 0
    const lastWeekVol = weekMap[lastWeek] || 0
    const volChange = lastWeekVol ? Math.round(((thisWeekVol - lastWeekVol) / lastWeekVol) * 100) : null

    return { prs, liftNames, weekLabels, weekVolumes, orm1Map, thisWeekWorkouts, thisWeekVol, volChange, prMap }
  }, [history])

  // Set default active lift once data loads
  useEffect(() => {
    if (stats && stats.liftNames.length && !activeLift) {
      // prefer common lifts, otherwise first available
      const preferred = ['squat', 'bench', 'deadlift', 'ohp', 'bench press']
      const found = preferred.find(l => stats.liftNames.includes(l))
      setActiveLift(found || stats.liftNames[0])
    }
  }, [stats, activeLift])

  // ── Weekly digest text ────────────────────────────────────────────────────

  const digest = useMemo(() => {
    if (!stats) return 'Log your first workout to see your weekly digest.'
    const { thisWeekWorkouts, volChange, prs } = stats
    const parts = []
    parts.push(`${thisWeekWorkouts.length} workout${thisWeekWorkouts.length !== 1 ? 's' : ''} this week.`)
    if (volChange !== null) {
      parts.push(volChange >= 0
        ? `Volume is up ${volChange}% vs last week — great consistency.`
        : `Volume is down ${Math.abs(volChange)}% vs last week.`)
    }
    if (prs.length) {
      const top = prs[0]
      parts.push(`Top PR: ${top[0]} at ${top[1].weight} kg.`)
    }
    return parts.join(' ')
  }, [stats])

  // ── Chart data for selected lift ──────────────────────────────────────────

  const liftChartData = useMemo(() => {
    if (!stats || !activeLift || !stats.orm1Map[activeLift]) return null
    const weekData = stats.orm1Map[activeLift]
    const weeks = Object.keys(weekData).sort().slice(-8)
    const color = LIFT_COLORS[activeLift] || '#3b82f6'
    return {
      labels: weeks.map(fmt),
      datasets: [{
        data: weeks.map(wk => weekData[wk]),
        borderColor: color,
        backgroundColor: color + '22',
        pointBackgroundColor: color,
        fill: true, tension: 0.4, pointRadius: 4,
      }],
    }
  }, [stats, activeLift])

  const volumeChartData = useMemo(() => {
    if (!stats) return null
    return {
      labels: stats.weekLabels.map(fmt),
      datasets: [{
        data: stats.weekVolumes,
        backgroundColor: '#3b82f633',
        borderColor: '#3b82f6',
        borderWidth: 2,
        borderRadius: 4,
      }],
    }
  }, [stats])

  // ── Delete handler ────────────────────────────────────────────────────────

  const handleDelete = async (e, workoutId) => {
    e.stopPropagation()
    if (deletingId) return
    if (!window.confirm('Delete this workout?')) return
    setDeletingId(workoutId)
    try {
      await deleteWorkout(workoutId)
      setHistory(prev => prev.filter(w => w.workout_id !== workoutId))
    } catch (err) {
      console.error('Failed to delete workout', err)
    } finally {
      setDeletingId(null)
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="page fade-in">
        <div className="page-header"><h1>Progress</h1></div>
        <div className="page-content" style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}>
          <div style={{ color: 'var(--muted)', fontSize: 14 }}>Loading your stats...</div>
        </div>
      </div>
    )
  }

  const historyDesc = [...history].sort((a, b) => b.date.localeCompare(a.date))

  return (
    <div className="page fade-in">
      <div className="page-header"><h1>Progress</h1></div>
      <div className="page-content">
        <div style={{ height: 14 }} />

        {/* ── AI weekly digest ── */}
        <AICard badge="Weekly Digest">{digest}</AICard>

        {/* ── Strength Progress ── */}
        {stats && stats.liftNames.length > 0 ? (
          <>
            <div style={{ padding: '0 16px' }}>
              <div className="card-title" style={{ marginBottom: 10 }}>Strength Progress (est. 1RM)</div>
              <div className="lift-btn-row" style={{ flexWrap: 'wrap', gap: 6 }}>
                {stats.liftNames.map(name => (
                  <button
                    key={name}
                    className={`lift-btn${activeLift === name ? ' active' : ''}`}
                    onClick={() => setActiveLift(name)}
                    style={{ textTransform: 'capitalize' }}
                  >
                    {name}
                  </button>
                ))}
              </div>
            </div>

            {liftChartData ? (
              <div className="card fade-in" style={{ marginTop: 0 }}>
                <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12, textTransform: 'capitalize' }}>
                  {activeLift} — estimated 1RM over time
                </div>
                <Line data={liftChartData} options={chartDefaults} height={130} />
              </div>
            ) : (
              <div className="card fade-in" style={{ marginTop: 0 }}>
                <div style={{ fontSize: 13, color: 'var(--muted)' }}>Not enough data for {activeLift} yet.</div>
              </div>
            )}
          </>
        ) : (
          <div className="card fade-in">
            <div style={{ color: 'var(--muted)', fontSize: 13 }}>Log strength workouts with sets to see progress charts.</div>
          </div>
        )}

        {/* ── Weekly Volume ── */}
        {volumeChartData && stats.weekVolumes.some(v => v > 0) ? (
          <div className="card fade-in">
            <div className="card-title">Weekly Volume (kg)</div>
            <Bar data={volumeChartData} options={volumeOptions} height={120} />
          </div>
        ) : null}

        {/* ── Personal Records ── */}
        {stats && stats.prs.length > 0 && (
          <div className="card fade-in">
            <div className="card-title">Personal Records</div>
            {stats.prs.map(([name, pr], i) => {
              const trophies = ['🥇', '🥈', '🥉', '🏅', '🏅', '🏅']
              return (
                <div key={name} className="pr-item">
                  <div className="trophy">{trophies[i] || '🏅'}</div>
                  <div className="pr-lift" style={{ textTransform: 'capitalize' }}>{name}</div>
                  <div className="pr-weight">{pr.weight} kg</div>
                  <div className="pr-date">{fmt(pr.date)}</div>
                </div>
              )
            })}
          </div>
        )}

        {/* ── Workout History ── */}
        <div style={{ padding: '0 16px', marginBottom: 14 }}>
          <div className="card-title" style={{ marginBottom: 10 }}>Workout History</div>

          {historyDesc.length === 0 && (
            <div style={{ color: 'var(--muted)', fontSize: 13, textAlign: 'center', padding: 16 }}>
              No workouts logged yet.
            </div>
          )}

          {historyDesc.map((w) => {
            const isExpanded = expandedId === w.workout_id
            const exercises = w.exercise || []
            const totalSets = exercises.reduce((n, ex) => n + (ex.SET?.length || 0), 0)
            const totalVolume = exercises.reduce((sum, ex) =>
              sum + (ex.SET || []).reduce((s, set) => s + set.weight * set.reps, 0), 0
            )
            return (
              <div
                key={w.workout_id}
                className="card fade-in"
                style={{ marginBottom: 10, cursor: 'pointer' }}
                onClick={() => setExpandedId(isExpanded ? null : w.workout_id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{fmt(w.date)}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2, textTransform: 'capitalize' }}>
                      {w.type || 'Strength'} · {w.duration} min · {w.calories_burned} cal
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button
                      onClick={(e) => handleDelete(e, w.workout_id)}
                      disabled={deletingId === w.workout_id}
                      style={{
                        background: 'none', border: 'none', cursor: 'pointer',
                        color: '#ef4444', fontSize: 14, padding: '4px 6px',
                        borderRadius: 6, lineHeight: 1,
                        opacity: deletingId === w.workout_id ? 0.4 : 1,
                      }}
                    >🗑</button>
                    <span style={{ color: 'var(--muted)', fontSize: 18 }}>{isExpanded ? '▲' : '▼'}</span>
                  </div>
                </div>

                {!isExpanded && (
                  <div style={{ marginTop: 8, fontSize: 12, color: 'var(--muted)' }}>
                    {exercises.length} exercise{exercises.length !== 1 ? 's' : ''} · {totalSets} sets · {Math.round(totalVolume).toLocaleString()} kg vol
                  </div>
                )}

                {isExpanded && (
                  <div style={{ marginTop: 12 }}>
                    {exercises.length === 0 && (
                      <div style={{ fontSize: 12, color: 'var(--muted)' }}>No exercises recorded.</div>
                    )}
                    {exercises.map((ex) => (
                      <div key={ex.exercise_id} style={{ marginBottom: 10 }}>
                        <div style={{ fontWeight: 600, fontSize: 13, textTransform: 'capitalize', marginBottom: 4 }}>
                          {ex.name}
                          <span style={{ fontWeight: 400, color: 'var(--muted)', marginLeft: 6, fontSize: 11 }}>
                            {ex.muscle_group}
                          </span>
                        </div>
                        {(ex.SET || []).map((s) => (
                          <div key={s.set_id} style={{
                            display: 'grid', gridTemplateColumns: '28px 1fr 1fr 1fr',
                            fontSize: 12, color: 'var(--muted)', padding: '2px 0',
                          }}>
                            <span>{s.set_num}</span>
                            <span>{s.weight} kg</span>
                            <span>{s.reps} reps</span>
                            <span>RPE {s.intensity}</span>
                          </div>
                        ))}
                      </div>
                    ))}
                    <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--muted)' }}>
                      {totalSets} sets · {Math.round(totalVolume).toLocaleString()} kg total volume
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

      </div>
    </div>
  )
}