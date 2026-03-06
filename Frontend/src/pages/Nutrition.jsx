// ─────────────────────────────────────────────────────────────────────────────
// Nutrition.jsx — Daily nutrition tracking page
//
// Shows the user's calorie and macro intake for the day vs their targets,
// plus a list of meals logged so far.
//
// Sections:
//   - AI Insight card: adaptive nutrition recommendation based on workout
//   - Daily summary: total calories consumed vs goal, calories remaining
//   - Macro progress bars: protein / carbs / fat (current vs target)
//   - Meal log: list of meals with food items and calories
//   - "Log Food" button (not yet wired)
//
// MacroBar is a local helper component — not exported because it's only
// used on this page.
//
// TODO: When backend is connected:
//   - Fetch meal list via GET /meals?date=today
//   - Fetch macro targets from user profile via GET /users/{user_id}
//   - "Log Food" should open a food search modal → GET /food-search/search
//   - After selecting food, POST to /food-search/save-by-name/{meal_id}
// ─────────────────────────────────────────────────────────────────────────────

import AICard from '../components/AICard'
import { mealsData } from '../data/mockData'

// ── MacroBar — reusable progress bar for a single macronutrient ──────────────
// Props:
//   label     — display name (e.g. "Protein")
//   current   — grams consumed so far
//   goal      — daily target in grams
//   fillClass — CSS class that sets the bar color (fill-blue / fill-orange / fill-purple)
function MacroBar({ label, current, goal, fillClass }) {
  // Cap at 100% so the bar doesn't overflow if user exceeds goal
  const pct = Math.min(100, Math.round((current / goal) * 100))
  return (
    <div className="macro-bar-wrap">
      <div className="macro-label-row">
        <span>{label}</span>
        <span>{current}g / {goal}g</span>
      </div>
      <div className="macro-bar">
        {/* Width is set inline as a percentage so it animates via CSS transition */}
        <div className={`macro-fill ${fillClass}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function Nutrition() {
  return (
    <div className="page fade-in">
      <div className="page-header"><h1>Nutrition</h1></div>
      <div className="page-content">
        <div style={{ height: 14 }} />

        {/* ── AI nutrition insight ── */}
        {/* TODO: Generate this from workout intensity + user macros via Groq */}
        <AICard>
          High-intensity leg day detected. You burned an estimated <strong>620 cal</strong>. Increase
          protein by <strong>20g</strong> and add 300 calories to support muscle repair.
        </AICard>

        {/* ── Daily calorie summary ── */}
        <div className="card fade-in">
          <div className="card-title">Daily Summary</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 14 }}>
            <div>
              {/* Total calories consumed today */}
              <div style={{ fontSize: 36, fontWeight: 900, lineHeight: 1 }}>1,840</div>
              <div style={{ fontSize: 13, color: 'var(--muted)' }}>/ 2,400 kcal</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 12, color: 'var(--muted)' }}>Remaining</div>
              {/* Remaining calories = goal - consumed */}
              <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--green)' }}>560</div>
            </div>
          </div>

          {/* ── Macro progress bars ── */}
          {/* Each bar shows current intake vs daily goal for that macro */}
          <MacroBar label="Protein" current={142} goal={180} fillClass="fill-blue" />
          <MacroBar label="Carbs"   current={195} goal={280} fillClass="fill-orange" />
          <MacroBar label="Fat"     current={58}  goal={75}  fillClass="fill-purple" />
        </div>

        {/* ── Today's meal log ── */}
        <div className="card fade-in">
          <div className="card-title">Today's Meals</div>
          {mealsData.map(meal => (
            <div key={meal.name} className="meal-item">
              {/* Colored emoji icon for each meal */}
              <div className="meal-icon" style={{ background: meal.bg }}>{meal.icon}</div>
              <div className="meal-info">
                <div className="meal-name">{meal.name}</div>
                <div className="meal-sub">{meal.sub}</div>
              </div>
              {/* Show calorie count, or "—" in muted grey if meal not logged yet */}
              <div className="meal-cal" style={!meal.cal ? { color: 'var(--muted)' } : {}}>
                {meal.cal ?? '—'}
              </div>
            </div>
          ))}
        </div>

        {/* TODO: Open food search modal on click */}
        <div style={{ padding: '0 16px 14px' }}>
          <button className="btn btn-primary btn-full">+ Log Food</button>
        </div>
      </div>
    </div>
  )
}
