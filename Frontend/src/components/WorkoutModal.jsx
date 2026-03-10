// ─────────────────────────────────────────────────────────────────────────────
// WorkoutModal.jsx — Post-workout summary sheet
//
// A bottom sheet modal that slides up when the user taps "Finish Workout".
// Shows a summary of the completed session and an AI recommendation.
// Currently all values are hardcoded mock data.
//
// Props:
//   onClose(wasSaved) — called when the user taps either button
//                       wasSaved=true  → "Save & Continue" was tapped
//                       wasSaved=false → "Discard Session" was tapped
//
// The parent (Workout.jsx) uses wasSaved to decide whether to show the
// green "Session Saved" banner after the modal closes.
//
// TODO: When backend is connected, "Save & Continue" should POST the workout
// data to the API before closing. The summary stats should be calculated from
// actual set data instead of being hardcoded here.
// ─────────────────────────────────────────────────────────────────────────────

export default function WorkoutModal({ onClose }) {
  return (
    // Full-screen dark overlay behind the sheet
    <div className="modal-overlay">

      {/* The actual bottom sheet — slides up via CSS animation (slideUp keyframe) */}
      <div className="modal-sheet">

        {/* Decorative drag handle bar at the top */}
        <div className="modal-handle" />

        <div className="modal-title">Session Complete!</div>

        {/* Session stats — TODO: calculate these from actual set inputs */}
        <div className="summary-stat">
          <span className="summary-stat-label">Total Sets</span>
          <span className="summary-stat-val">18 sets</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-label">Total Volume</span>
          <span className="summary-stat-val" style={{ color: 'var(--accent)' }}>12,450 lbs</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-label">vs Last Session</span>
          <span className="summary-stat-val" style={{ color: 'var(--green)' }}>+8%</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-label">Duration</span>
          <span className="summary-stat-val">58 min</span>
        </div>

        {/* AI recommendation section — TODO: replace with real Groq response */}
        <div style={{ margin: '18px 0 16px' }}>
          <div className="ai-badge" style={{ marginBottom: 8 }}>AI Recommendation</div>
          <div className="ai-text" style={{ fontSize: 13 }}>
            Volume up 8%. Bench press velocity improved.{' '}
            <strong>Increase bench weight by 5 lbs next session.</strong> Great work — recovery score green.
          </div>
        </div>

        {/* onClose(true) = save, onClose(false) = discard */}
        <button className="btn btn-primary btn-full" onClick={() => onClose(true)} style={{ marginBottom: 10 }}>
          Save &amp; Continue
        </button>
        <button className="btn btn-ghost btn-full" onClick={() => onClose(false)}>
          Discard Session
        </button>
      </div>
    </div>
  )
}
