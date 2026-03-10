// ─────────────────────────────────────────────────────────────────────────────
// Recovery.jsx — Sleep and recovery tracking page
//
// Shows the user's current recovery score and allows them to log sleep data
// and stress level. The bar chart visualizes the past 7 nights of sleep.
//
// Sections:
//   - Recovery score ring: SVG circle showing score out of 100
//   - AI Recovery Alert: explains what's causing low recovery
//   - Sleep log: dropdowns for hours slept and quality rating
//   - Stress level pills: Low / Medium / High selector (interactive)
//   - 7-day sleep trend: bar chart color-coded by sleep quality
//
// State:
//   stress — currently selected stress level ('low' | 'medium' | 'high')
//            Clicking a pill updates this and adds the .selected CSS class
//
// sleepOptions extends chartDefaults to:
//   - Force y-axis range 0–10 (hours)
//   - Format y-axis tick labels with 'h' suffix (e.g. "7h")
//
// TODO: When backend is connected:
//   - Recovery score → calculated from sleep + stress data
//   - Sleep/quality dropdowns → POST /recovery (or similar endpoint)
//   - Stress pill selection → include in recovery POST
//   - Chart data → GET sleep history for the past 7 days
// ─────────────────────────────────────────────────────────────────────────────

import { useState } from 'react'
import { Bar } from 'react-chartjs-2'
import AICard from '../components/AICard'
import { chartDefaults, sleepChartData } from '../data/mockData'

// Extends chartDefaults specifically for the sleep bar chart:
// - Locks y-axis to 0–10 hours range
// - Adds 'h' suffix to y-axis tick labels
const sleepOptions = {
  ...chartDefaults,
  scales: {
    ...chartDefaults.scales,
    y: {
      ...chartDefaults.scales.y,
      min: 0, max: 10,
      ticks: { ...chartDefaults.scales.y.ticks, callback: v => v + 'h' },
    },
  },
}

export default function Recovery() {
  // Tracks which stress pill is selected — defaults to 'high' to match mock data
  const [stress, setStress] = useState('high')

  return (
    <div className="page fade-in">
      <div className="page-header"><h1>Recovery</h1></div>
      <div className="page-content">
        <div style={{ height: 14 }} />

        {/* ── Recovery score ring ── */}
        {/* SVG circle ring showing 42/100.
            strokeDasharray = full circumference of circle with r=50 → 2π×50 ≈ 314.16
            strokeDashoffset = how much to "hide" → 314.16 × (1 - 0.42) ≈ 182.21
            The SVG is rotated -90deg so the arc starts at the top */}
        <div className="card fade-in">
          <div className="score-circle">
            <div className="score-ring">
              <svg width="120" height="120" viewBox="0 0 120 120">
                {/* Grey background track */}
                <circle cx="60" cy="60" r="50" fill="none" stroke="#2a3347" strokeWidth="10"/>
                {/* Orange filled arc — offset controls how much is shown */}
                <circle cx="60" cy="60" r="50" fill="none" stroke="#f59e0b" strokeWidth="10"
                  strokeDasharray="314.16" strokeDashoffset="188.5" strokeLinecap="round"/>
              </svg>
              {/* Score number centered inside the ring */}
              <div className="score-center">
                <div className="score-num">42</div>
                <div className="score-lbl">/ 100</div>
              </div>
            </div>
            <div className="score-status">Low Recovery</div>
          </div>
        </div>

        {/* ── AI recovery alert ── */}
        {/* TODO: Generate from actual sleep + stress data via Groq */}
        <AICard badge="AI Recovery Alert">
          Your recovery score is <strong>42/100</strong>. Sleep was 4.8 hours last night and stress is
          high. Today's workout volume has been <strong>reduced by 3 sets</strong> to prevent overtraining.
        </AICard>

        {/* ── Sleep log inputs ── */}
        <div className="card fade-in">
          <div className="card-title">Last Night's Sleep</div>
          <div className="sleep-input-row">
            {/* Hours slept selector */}
            <div className="sleep-input-wrap">
              <div className="sleep-label">Hours Slept</div>
              <select className="sleep-select" defaultValue="4.8 hours">
                <option>4.8 hours</option>
                <option>5.0 hours</option>
                <option>6.0 hours</option>
                <option>7.0 hours</option>
                <option>8.0 hours</option>
              </select>
            </div>
            {/* Sleep quality rating selector */}
            <div className="sleep-input-wrap">
              <div className="sleep-label">Quality</div>
              <select className="sleep-select" defaultValue="2 / 5 - Poor">
                <option>2 / 5 – Poor</option>
                <option>3 / 5 – Fair</option>
                <option>4 / 5 – Good</option>
                <option>5 / 5 – Great</option>
              </select>
            </div>
          </div>

          {/* ── Stress level pills ── */}
          {/* Clicking a pill sets the stress state and applies .selected styling */}
          <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '.06em' }}>
            Stress Level Today
          </div>
          <div className="stress-pills">
            {['Low', 'Medium', 'High'].map(level => (
              <div
                key={level}
                className={`stress-pill${stress === level.toLowerCase() ? ' selected' : ''}`}
                onClick={() => setStress(level.toLowerCase())}
              >
                {level}
              </div>
            ))}
          </div>
        </div>

        {/* ── 7-day sleep trend bar chart ── */}
        {/* Bar colors come from the backgroundColor function in sleepChartData (mockData.js) */}
        <div className="card fade-in">
          <div className="card-title">7-Day Sleep Trend</div>
          <Bar data={sleepChartData} options={sleepOptions} height={120} />
        </div>
      </div>
    </div>
  )
}
