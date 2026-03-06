// ─────────────────────────────────────────────────────────────────────────────
// Dashboard.jsx — Main home screen (shown after login)
//
// The hub of the app. Shows a summary of the user's current state across
// all tracked areas: recovery, workouts, nutrition, and strength progress.
//
// Sections:
//   - Hero bar: greeting, today's date, recovery score pill
//   - AI Insight card: personalized recommendation from the AI coach
//   - Weekly ring: workouts completed vs planned (SVG progress ring)
//   - Stats row: weekly volume, bench 1RM estimate, calories today
//   - Squat 1RM trend chart: 4-week line chart
//   - Quick Actions: tap shortcuts to other pages
//
// Props:
//   goTo — navigation function from App.jsx
//
// TODO: All data here is hardcoded. Replace with:
//   - Recovery score → GET /analytics/workouts/summary
//   - Stats row      → GET /analytics/calories/net/{date} + workout summary
//   - Chart data     → GET /analytics/exercises/progress/squat
// ─────────────────────────────────────────────────────────────────────────────

import { Line } from 'react-chartjs-2'
import AICard from '../components/AICard'
import { chartDefaults, dashChartData } from '../data/mockData'

export default function Dashboard({ goTo }) {
  return (
    <div className="page fade-in">

      {/* ── Hero bar ── */}
      <div className="dash-hero">
        <div className="dash-greeting">Wednesday, Feb 25</div>  {/* TODO: use new Date() */}
        <div className="dash-name">Hey, Dylan</div>             {/* TODO: use logged-in user's name */}
        {/* Green pill shows recovery status — color should change based on score */}
        <div className="recovery-pill">
          <div className="pulse" />
          Recovery Score: 85/100 · Green Light   {/* TODO: fetch from analytics */}
        </div>
      </div>

      {/* page-content handles scroll and adds bottom padding for the nav bar */}
      <div className="page-content">
        <div style={{ height: 14 }} />

        {/* ── AI Insight card ── */}
        {/* TODO: Replace with real AI-generated insight from Groq */}
        <AICard>
          Your squat 1RM has increased <strong>15 lbs</strong> over the past 3 weeks. You're ready to
          attempt <strong>275 lbs</strong>. Recovery score is 85/100 — green light to push today.
        </AICard>

        {/* ── Weekly progress ring ── */}
        {/* SVG circle ring: strokeDashoffset controls how much of the ring is filled.
            Full circle circumference = 2π × 32 ≈ 200.96
            4/5 done = 80% filled → offset = 200.96 × 0.2 = ~50.24 */}
        <div className="card fade-in">
          <div className="card-title">This Week</div>
          <div className="ring-row">
            <div className="ring-wrap">
              <svg width="80" height="80" viewBox="0 0 80 80">
                {/* Background track circle */}
                <circle cx="40" cy="40" r="32" fill="none" stroke="#2a3347" strokeWidth="8"/>
                {/* Filled progress arc */}
                <circle cx="40" cy="40" r="32" fill="none" stroke="#3b82f6" strokeWidth="8"
                  strokeDasharray="200.96" strokeDashoffset="50.24" strokeLinecap="round"/>
              </svg>
              <div className="ring-center">4<span>/ 5</span></div>
            </div>
            <div className="ring-info">
              <h3>4 of 5 Workouts Done</h3>
              <p>
                Today: <strong style={{ color: 'var(--text)' }}>Upper Body – Push</strong>
                <br />Chest · Shoulders · Triceps
              </p>
            </div>
          </div>
        </div>

        {/* ── Stats row ── three quick-glance numbers ── */}
        {/* TODO: fetch all three from API */}
        <div className="stat-row">
          <div className="stat-card">
            <div className="stat-label">Weekly Volume</div>
            <div className="stat-val blue">42.5k</div>
            <div className="stat-sub">lbs · +8% vs last week</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Bench 1RM est.</div>
            <div className="stat-val green">225</div>
            <div className="stat-sub">lbs · +5 lbs</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Calories Today</div>
            <div className="stat-val orange">1,840</div>
            <div className="stat-sub">/ 2,400 goal</div>
          </div>
        </div>

        {/* ── Squat 1RM trend chart ── */}
        {/* height={120} sets the canvas pixel height; Chart.js scales it responsively */}
        <div className="card fade-in">
          <div className="card-title">Squat 1RM Trend – 4 Weeks</div>
          <Line data={dashChartData} options={chartDefaults} height={120} />
        </div>

        {/* ── Quick action buttons ── */}
        {/* Shortcut grid to navigate to the four main input pages */}
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
