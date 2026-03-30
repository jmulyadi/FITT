// ─────────────────────────────────────────────────────────────────────────────
// Workout.jsx — Active workout tracking page (backend connected)
//
// On "Finish Workout":
//   1. POST /workouts/          → creates the workout, gets workout_id
//   2. POST /workouts/{id}/exercises → for each exercise, gets exercise_id
//   3. POST /workouts/{id}/exercises/{ex_id}/sets → for each completed set
//
// "Add Exercise" searches ExerciseDB via GET /workouts/exercise-search?name=
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useRef } from "react";
import { createWorkout, addExercise, addSet as apiAddSet, searchExercises } from "../api/workouts";
import WorkoutModal from "../components/WorkoutModal";
import { initialExercises } from "../data/mockData";

function formatTime(sec) {
  const m = Math.floor(Math.abs(sec) / 60);
  const s = Math.abs(sec) % 60;
  return (sec < 0 ? "+" : "") + m + ":" + String(s).padStart(2, "0");
}

// Today's date as YYYY-MM-DD
function today() {
  return new Date().toISOString().split("T")[0];
}

export default function Workout({ goTo }) {
  const [exercises, setExercises] = useState(initialExercises);
  const [timerSec, setTimerSec] = useState(90);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef(null);
  const [showModal, setShowModal] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Workout summary passed to modal after save
  const [workoutSummary, setWorkoutSummary] = useState(null);

  // Track when the workout started so we can calculate duration
  const startTimeRef = useRef(Date.now());

  const startTimer = () => {
    if (running) {
      clearInterval(intervalRef.current);
      setRunning(false);
      setTimerSec(90);
      return;
    }
    setTimerSec(90);
    setRunning(true);
    intervalRef.current = setInterval(() => {
      setTimerSec((prev) => {
        if (prev <= -60) {
          clearInterval(intervalRef.current);
          setRunning(false);
          return prev;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const deleteExercise = (exIdx) => {
    setExercises((prev) => prev.filter((_, i) => i !== exIdx));
  };

  const deleteSet = (exIdx, setIdx) => {
    setExercises((prev) =>
      prev.map((ex, i) =>
        i !== exIdx
          ? ex
          : { ...ex, sets: ex.sets.filter((_, j) => j !== setIdx) }
      )
    );
  };

  const addSet = (exIdx) => {
    setExercises((prev) =>
      prev.map((ex, i) =>
        i !== exIdx
          ? ex
          : { ...ex, sets: [...ex.sets, { weight: "", reps: "", rpe: "" }] }
      )
    );
  };

  const updateSet = (exIdx, setIdx, field, value) => {
    setExercises((prev) =>
      prev.map((ex, i) =>
        i !== exIdx
          ? ex
          : {
              ...ex,
              sets: ex.sets.map((s, j) =>
                j !== setIdx ? s : { ...s, [field]: value }
              ),
            }
      )
    );
  };

  // Exercise search picker state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showPicker, setShowPicker] = useState(false);

  const handleOpenPicker = () => {
    setSearchQuery("");
    setSearchResults([]);
    setShowPicker(true);
  };

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (!query.trim()) { setSearchResults([]); return; }
    setSearchLoading(true);
    try {
      const results = await searchExercises(query, 15);
      setSearchResults(results.exercises || results);
    } catch (err) {
      console.error(err);
    } finally {
      setSearchLoading(false);
    }
  };

  const handlePickExercise = (ex) => {
    setExercises((prev) => [
      ...prev,
      {
        name: ex.name.charAt(0).toUpperCase() + ex.name.slice(1),
        muscles: [ex.target || ex.bodyPart || "Unknown"],
        muscleGroup: ex.target || ex.bodyPart || "Unknown",
        sets: [
          { weight: "", reps: "", rpe: "" },
          { weight: "", reps: "", rpe: "" },
          { weight: "", reps: "", rpe: "" },
        ],
        prev: "New exercise",
      },
    ]);
    setShowPicker(false);
    setSearchQuery("");
    setSearchResults([]);
  };

  // ── Save workout to backend ───────────────────────────────────────────────
  const handleFinish = async (wasSaved) => {
    if (!wasSaved) {
      setShowModal(false);
      return;
    }

    try {
      setSaving(true);
      setSaveError(null);

      // Calculate duration in minutes
      const durationMin = Math.max(
        1,
        Math.round((Date.now() - startTimeRef.current) / 60000)
      );

      // Count total completed sets (both weight and reps filled in)
      const completedSets = exercises.flatMap((ex) =>
        ex.sets.filter((s) => s.weight && s.reps)
      );
      const totalVolume = completedSets.reduce(
        (sum, s) => sum + parseFloat(s.weight) * parseInt(s.reps),
        0
      );

      // Rough calorie estimate: 5 cal per set
      const caloriesBurned = Math.round(completedSets.length * 5);

      // 1. Create the workout
      const { workout_id } = await createWorkout({
        date: today(),
        duration: durationMin,
        calories_burned: caloriesBurned,
        type: "strength",
      });

      // 2. Save each exercise and its completed sets
      for (const ex of exercises) {
        const completedExSets = ex.sets.filter((s) => s.weight && s.reps);
        if (!completedExSets.length) continue; // skip exercises with no sets filled

        const { exercise_id } = await addExercise(
          workout_id,
          ex.name,
          ex.muscleGroup || ex.muscles?.[0] || "Unknown"
        );

        // 3. Save each set
        for (let i = 0; i < completedExSets.length; i++) {
          const s = completedExSets[i];
          await apiAddSet(
            workout_id,
            exercise_id,
            i + 1,
            parseInt(s.reps),
            parseFloat(s.weight),
            Math.round(parseFloat(s.rpe) || 7) // default intensity 7 if no RPE
          );
        }
      }

      setWorkoutSummary({
        totalSets: completedSets.length,
        totalVolume: Math.round(totalVolume),
        duration: durationMin,
        workoutId: workout_id,
      });

      setShowModal(false);
      setSaved(true);
    } catch (err) {
      console.error(err);
      setSaveError("Failed to save workout. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 2 }}>
            Strength Session
          </div>
          <h1>Today's Session</h1>
        </div>
        <div className="badge">In Progress</div>
      </div>

      <div className="page-content">
        <div style={{ height: 14 }} />

        {/* ── Post-save banner ── */}
        {saved && workoutSummary && (
          <div className="finish-banner fade-in">
            <h3>Session Saved ✓</h3>
            <p>
              {workoutSummary.totalSets} sets · {workoutSummary.totalVolume.toLocaleString()} lbs total volume · {workoutSummary.duration} min
            </p>
          </div>
        )}

        {/* ── Save error ── */}
        {saveError && (
          <div className="form-error" style={{ margin: "0 16px 12px" }}>
            {saveError}
          </div>
        )}

        {/* ── Rest timer ── */}
        <div className="rest-timer">
          <div>
            <div className="timer-label">Rest Timer</div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>
              90s recommended
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div
              className="timer-val"
              style={{ color: timerSec <= 0 ? "var(--green)" : "var(--text)" }}
            >
              {formatTime(timerSec)}
            </div>
            <button
              className="btn btn-ghost"
              style={{ fontSize: 11, padding: "4px 10px", marginTop: 4 }}
              onClick={startTimer}
            >
              {running ? "Reset" : "Start"}
            </button>
          </div>
        </div>

        {/* ── Exercise cards ── */}
        {exercises.map((ex, exIdx) => (
          <div key={exIdx} className="exercise-card fade-in">
            <div className="ex-header">
              <div style={{ flex: 1 }}>
                <div className="ex-name">{ex.name}</div>
                <div style={{ marginTop: 3, display: "flex", gap: 6 }}>
                  {ex.muscles.map((m) => (
                    <span key={m} className="muscle-tag">{m}</span>
                  ))}
                </div>
              </div>
              <button
                onClick={() => deleteExercise(exIdx)}
                style={{
                  background: "none", border: "none", cursor: "pointer",
                  color: "var(--muted)", fontSize: 18, padding: "0 4px",
                  lineHeight: 1,
                }}
                title="Remove exercise"
              >
                ✕
              </button>
            </div>

            <div className="sets-header" style={{ gridTemplateColumns: "28px 1fr 1fr 1fr 28px" }}>
              <span>#</span>
              <span>Weight</span>
              <span>Reps</span>
              <span>RPE</span>
              <span />
            </div>

            {ex.sets.map((s, setIdx) => {
              const empty = !s.weight && !s.reps;
              return (
                <div key={setIdx} className="set-row" style={{ gridTemplateColumns: "28px 1fr 1fr 1fr 28px" }}>
                  <div className={`set-num${empty ? " empty" : ""}`}>
                    {setIdx + 1}
                  </div>
                  <input
                    className="set-input"
                    value={s.weight}
                    placeholder="—"
                    type="number"
                    onChange={(e) => updateSet(exIdx, setIdx, "weight", e.target.value)}
                  />
                  <input
                    className="set-input"
                    value={s.reps}
                    placeholder="—"
                    type="number"
                    onChange={(e) => updateSet(exIdx, setIdx, "reps", e.target.value)}
                  />
                  <input
                    className="set-input"
                    value={s.rpe}
                    placeholder="—"
                    type="number"
                    onChange={(e) => updateSet(exIdx, setIdx, "rpe", e.target.value)}
                  />
                  <button
                    onClick={() => deleteSet(exIdx, setIdx)}
                    style={{
                      background: "none", border: "none", cursor: "pointer",
                      color: "var(--muted)", fontSize: 15, padding: 0,
                      lineHeight: 1, opacity: 0.6,
                    }}
                    title="Remove set"
                  >
                    ✕
                  </button>
                </div>
              );
            })}

            <button
              className="btn btn-ghost"
              style={{ width: "100%", marginTop: 6, fontSize: 12, padding: "6px 0" }}
              onClick={() => addSet(exIdx)}
            >
              + Add Set
            </button>

            <div className="prev-stats">{ex.prev}</div>
          </div>
        ))}

        {/* ── Footer actions ── */}
        <div style={{ padding: "0 16px", display: "flex", gap: 10, marginBottom: 14 }}>
          <button
            className="btn btn-ghost"
            style={{ flex: 1 }}
            onClick={handleOpenPicker}
          >
            + Add Exercise
          </button>
          <button
            className="btn btn-green"
            style={{ flex: 1 }}
            onClick={() => setShowModal(true)}
            disabled={saving}
          >
            {saving ? "Saving..." : "Finish Workout"}
          </button>
        </div>
      </div>

      {showModal && (
        <WorkoutModal
          exercises={exercises}
          onClose={handleFinish}
          saving={saving}
        />
      )}

      {/* ── Exercise Picker Sheet ── */}
      {showPicker && (
        <div
          style={{
            position: "fixed", inset: 0, zIndex: 200,
            background: "rgba(0,0,0,0.6)",
            display: "flex", alignItems: "flex-end",
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowPicker(false); }}
        >
          <div style={{
            background: "var(--card)",
            borderRadius: "18px 18px 0 0",
            width: "100%",
            maxHeight: "80vh",
            display: "flex",
            flexDirection: "column",
            padding: "20px 16px 0",
          }}>
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <h3 style={{ margin: 0, fontSize: 17 }}>Add Exercise</h3>
              <button
                className="btn btn-ghost"
                style={{ padding: "4px 12px", fontSize: 13 }}
                onClick={() => setShowPicker(false)}
              >
                Cancel
              </button>
            </div>

            {/* Search input */}
            <input
              autoFocus
              type="text"
              className="set-input"
              placeholder="Search exercises (e.g. bench, squat, curl)"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 14px",
                fontSize: 15,
                borderRadius: 10,
                border: "1.5px solid var(--border)",
                background: "var(--bg)",
                color: "var(--text)",
                marginBottom: 12,
                boxSizing: "border-box",
              }}
            />

            {/* Results list */}
            <div style={{ overflowY: "auto", flex: 1, paddingBottom: 24 }}>
              {searchLoading && (
                <div style={{ textAlign: "center", color: "var(--muted)", padding: 24, fontSize: 14 }}>
                  Searching...
                </div>
              )}
              {!searchLoading && searchQuery && searchResults.length === 0 && (
                <div style={{ textAlign: "center", color: "var(--muted)", padding: 24, fontSize: 14 }}>
                  No results for "{searchQuery}"
                </div>
              )}
              {!searchLoading && !searchQuery && (
                <div style={{ textAlign: "center", color: "var(--muted)", padding: 24, fontSize: 14 }}>
                  Type to search exercises
                </div>
              )}
              {searchResults.map((ex, i) => (
                <div
                  key={ex.id || i}
                  onClick={() => handlePickExercise(ex)}
                  style={{
                    padding: "12px 4px",
                    borderBottom: "1px solid var(--border)",
                    cursor: "pointer",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, textTransform: "capitalize" }}>
                      {ex.name}
                    </div>
                    <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2, textTransform: "capitalize" }}>
                      {ex.bodyPart} · {ex.target} · {ex.equipment}
                    </div>
                  </div>
                  <span style={{ color: "var(--green)", fontSize: 20, paddingLeft: 12 }}>+</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}