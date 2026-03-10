// ─────────────────────────────────────────────────────────────────────────────
// Progress.jsx — Strength progress and analytics page
//
// Shows long-term training trends to help users visualize improvement.
//
// Sections:
//   - AI Weekly Digest: summary of the week's highlights
//   - Lift selector: tab buttons to switch between squat/bench/deadlift/ohp
//   - Strength progress chart: estimated 1RM over 8 weeks for the selected lift
//   - Weekly volume chart: total lbs lifted per week over 8 weeks
//   - Personal records list: all-time PRs with trophy icons
//
// State:
//   activeLift — which lift's chart is currently displayed (default: 'squat')
//               Clicking a lift button updates this and re-renders the chart
//               with new data and color from liftData in mockData.js
//
// volumeOptions extends chartDefaults to format y-axis labels as "32k", "40k", etc.
//
// TODO: When backend is connected:
//   - Progress chart → GET /analytics/exercises/progress/{exercise_name}
//   - Volume chart   → GET /analytics/workouts/summary with date range
//   - PR data        → derive from max weight per exercise across all sets
// ─────────────────────────────────────────────────────────────────────────────

import { useState } from 'react'
import { Line, Bar } from 'react-chartjs-2'
import AICard from '../components/AICard'
import { chartDefaults, liftData, weeks8, volumeChartData, prData } from '../data/mockData'

// Extends chartDefaults for the volume bar chart:
// Formats y-axis ticks as "32k" instead of "32000"
const volumeOptions = {
  ...chartDefaults,
  scales: {
    ...chartDefaults.scales,
    y: {
      ...chartDefaults.scales.y,
      ticks: { ...chartDefaults.scales.y.ticks, callback: v => (v / 1000).toFixed(0) + 'k' },
    },
  },
}

export default function Progress() {
  // Which lift is currently selected — drives the chart data and color
  const [activeLift, setActiveLift] = useState('squat')

  // Build the chart data object for the currently selected lift
  const lift = liftData[activeLift]
  const progressChartData = {
    labels: weeks8,
    datasets: [{
      data: lift.data,
      borderColor: lift.color,
      backgroundColor: lift.color + '22',  // '22' appended = ~14% opacity hex
      pointBackgroundColor: lift.color,
      fill: true, tension: 0.4, pointRadius: 4,
    }],
  }

  return (
    <div className="page fade-in">
      <div className="page-header"><h1>Progress</h1></div>
      <div className="page-content">
        <div style={{ height: 14 }} />

        {/* ── AI weekly digest ── */}
        {/* TODO: Replace with real summary generated from workout data via Groq */}
        <AICard badge="Weekly Digest">
          This week you hit a new <strong>squat PR</strong>. Bench is trending up +5 lbs. Recovery has
          been inconsistent — prioritize sleep this weekend to maintain momentum.
        </AICard>

        {/* ── Lift selector buttons ── */}
        {/* Iterates over liftData keys to generate a button for each lift.
            The active lift gets the .active CSS class (blue background). */}
        <div style={{ padding: '0 16px 0' }}>
          <div className="card-title" style={{ marginBottom: 10 }}>Strength Progress</div>
          <div className="lift-btn-row">
            {Object.entries(liftData).map(([key]) => (
              <button
                key={key}
                className={`lift-btn${activeLift === key ? ' active' : ''}`}
                onClick={() => setActiveLift(key)}
              >
                {/* Capitalize first letter of lift key for display */}
                {key.charAt(0).toUpperCase() + key.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* ── Estimated 1RM line chart ── */}
        {/* Re-renders whenever activeLift changes, showing new data + color */}
        <div className="card fade-in" style={{ marginTop: 0 }}>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
            {lift.label} over 8 weeks
          </div>
          <Line data={progressChartData} options={chartDefaults} height={130} />
        </div>

        {/* ── Weekly volume bar chart ── */}
        {/* Shows total lbs lifted per week — a proxy for training load */}
        <div className="card fade-in">
          <div className="card-title">Weekly Volume (lbs)</div>
          <Bar data={volumeChartData} options={volumeOptions} height={120} />
        </div>

        {/* ── Personal records list ── */}
        {/* TODO: Derive PRs by querying max weight per exercise from the sets table */}
        <div className="card fade-in">
          <div className="card-title">Personal Records</div>
          {prData.map(pr => (
            <div key={pr.lift} className="pr-item">
              <div className="trophy">{pr.trophy}</div>
              <div className="pr-lift">{pr.lift}</div>
              <div className="pr-weight">{pr.weight}</div>
              <div className="pr-date">{pr.date}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
