// ─────────────────────────────────────────────────────────────────────────────
// AICard.jsx — Reusable AI insight card
//
// Used on Dashboard, Nutrition, Recovery, and Progress pages to display
// AI-generated recommendations. Currently shows hardcoded text — when the
// backend is connected, the content will come from POST /ai/chat (Groq API).
//
// Props:
//   badge    — label shown in the blue pill at the top (default: 'AI Insight')
//   children — the insight text/JSX rendered below the badge
//
// Usage:
//   <AICard>Your squat is trending up...</AICard>
//   <AICard badge="AI Recovery Alert">Sleep was low...</AICard>
// ─────────────────────────────────────────────────────────────────────────────

export default function AICard({ badge = 'AI Insight', children }) {
  return (
    <div className="card ai-card fade-in">
      {/* Blue pill badge at the top with a small icon */}
      <div className="ai-badge">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        {badge}
      </div>

      {/* The actual insight message — accepts JSX so text can include <strong> etc. */}
      <div className="ai-text">{children}</div>
    </div>
  )
}
