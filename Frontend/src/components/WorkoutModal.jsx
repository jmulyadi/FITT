// ─────────────────────────────────────────────────────────────────────────────
// WorkoutModal.jsx — Post-workout summary sheet (backend connected)
//
// Shows a live summary calculated from actual set data before saving.
// Props:
//   exercises — the exercises array from Workout.jsx state
//   saving    — bool, disables buttons while the API calls are in flight
//   onClose(wasSaved) — true = save & POST to backend, false = discard
// ─────────────────────────────────────────────────────────────────────────────

export default function WorkoutModal({ exercises = [], onClose, saving }) {
  // Calculate summary from actual set data
  const completedSets = exercises.flatMap((ex) =>
    ex.sets.filter((s) => s.weight && s.reps)
  );

  const totalVolume = completedSets.reduce(
    (sum, s) => sum + parseFloat(s.weight) * parseInt(s.reps),
    0
  );

  const totalSets = completedSets.length;
  const totalExercises = exercises.filter((ex) =>
    ex.sets.some((s) => s.weight && s.reps)
  ).length;

  return (
    <div className="modal-overlay">
      <div className="modal-sheet">
        <div className="modal-handle" />
        <div className="modal-title">Session Complete!</div>

        <div className="summary-stat">
          <span className="summary-stat-label">Exercises</span>
          <span className="summary-stat-val">{totalExercises}</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-label">Total Sets</span>
          <span className="summary-stat-val">{totalSets} sets</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-label">Total Volume</span>
          <span className="summary-stat-val" style={{ color: "var(--accent)" }}>
            {totalVolume.toLocaleString()} lbs
          </span>
        </div>

        {totalSets === 0 && (
          <div style={{ color: "var(--muted)", fontSize: 13, margin: "8px 0" }}>
            No completed sets yet — fill in weight and reps to log them.
          </div>
        )}

        <button
          className="btn btn-primary btn-full"
          onClick={() => onClose(true)}
          disabled={saving || totalSets === 0}
          style={{ marginBottom: 10, marginTop: 18 }}
        >
          {saving ? "Saving..." : "Save & Continue"}
        </button>
        <button
          className="btn btn-ghost btn-full"
          onClick={() => onClose(false)}
          disabled={saving}
        >
          Discard Session
        </button>
      </div>
    </div>
  );
}