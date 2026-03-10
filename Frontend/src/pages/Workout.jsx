// ─────────────────────────────────────────────────────────────────────────────
// Workout.jsx — Active workout tracking page
//
// Allows users to log sets for each exercise during a session.
// Features:
//   - Editable set inputs (weight / reps / RPE) stored in component state
//   - 90-second rest timer with Start/Reset toggle
//   - "Finish Workout" button opens the WorkoutModal summary sheet
//   - Green "Session Saved" banner appears after saving via the modal
//
// State:
//   exercises  — array of exercise objects (from mockData), each with a sets array.
//                Inputs are controlled — every keystroke updates this state.
//   timerSec   — current timer countdown value in seconds (starts at 90)
//   running    — whether the timer interval is active
//   showModal  — controls WorkoutModal visibility
//   saved      — whether the session was saved (shows banner if true)
//   intervalRef — useRef holds the setInterval ID so we can clear it on reset
//
// TODO: When backend is connected:
//   - Load today's planned workout via GET /workouts
//   - On "Save", POST workout → POST exercises → POST sets for each set row
//   - "Add Exercise" should open a search modal hitting GET /exercise-search/search
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useRef } from "react";
import { searchExercises } from "../api/workouts";
import WorkoutModal from "../components/WorkoutModal";
import { initialExercises } from "../data/mockData";

// Converts seconds to "M:SS" format. Negative values (overtime) show as "+M:SS"
function formatTime(sec) {
  const m = Math.floor(Math.abs(sec) / 60);
  const s = Math.abs(sec) % 60;
  return (sec < 0 ? "+" : "") + m + ":" + String(s).padStart(2, "0");
}
const addExercise = async () => {
  try {
    const name = prompt("Search exercise");

    if (!name) return;

    const results = await searchExercises(name);

    if (!results.length) {
      alert("No exercises found");
      return;
    }

    const ex = results[0];

    const newExercise = {
      name: ex.name,
      muscles: [ex.target],
      sets: [
        { weight: "", reps: "", rpe: "" },
        { weight: "", reps: "", rpe: "" },
        { weight: "", reps: "", rpe: "" },
      ],
      prev: "New exercise",
    };

    setExercises((prev) => [...prev, newExercise]);
  } catch (err) {
    console.error(err);
    alert("Error searching exercises");
  }
};
export default function Workout() {
  // exercises holds the full list including live-edited set values
  const [exercises, setExercises] = useState(initialExercises);

  // Rest timer state
  const [timerSec, setTimerSec] = useState(90); // starts at 90s
  const [running, setRunning] = useState(false);
  const intervalRef = useRef(null); // holds the interval ID

  // Modal and post-save banner state
  const [showModal, setShowModal] = useState(false);
  const [saved, setSaved] = useState(false);

  // Starts the countdown from 90s. If already running, resets it instead.
  // Timer continues past 0 into negative (overtime) for up to 60 extra seconds.
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
          // Auto-stop after 60s of overtime
          clearInterval(intervalRef.current);
          setRunning(false);
          return prev;
        }
        return prev - 1;
      });
    }, 1000);
  };

  // Updates a single field (weight, reps, or rpe) for a specific set
  // within a specific exercise. Uses immutable spread to avoid mutating state.
  const updateSet = (exIdx, setIdx, field, value) => {
    setExercises((prev) =>
      prev.map((ex, i) =>
        i !== exIdx
          ? ex
          : {
              ...ex,
              sets: ex.sets.map((s, j) =>
                j !== setIdx ? s : { ...s, [field]: value },
              ),
            },
      ),
    );
  };

  // Called by WorkoutModal when the user taps Save or Discard
  // wasSaved=true shows the green banner; wasSaved=false just closes the modal
  const handleModalClose = (wasSaved) => {
    setShowModal(false);
    if (wasSaved) setSaved(true);
  };

  return (
    <div className="page fade-in">
      {/* ── Page header ── */}
      <div className="page-header">
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 2 }}>
            Upper Body – Push
          </div>
          <h1>Today's Session</h1>
        </div>
        <div className="badge">In Progress</div>
      </div>

      <div className="page-content">
        <div style={{ height: 14 }} />

        {/* ── Post-save banner — only visible after modal "Save" is tapped ── */}
        {saved && (
          <div className="finish-banner fade-in">
            <h3>Session Saved</h3>
            <p>
              Volume: 12,450 lbs (+8%). Bench press velocity improved.{" "}
              <strong>Increase bench by 5 lbs next session.</strong>
            </p>
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
            {/* Timer turns green when it hits 0 to signal rest is done */}
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
        {/* Renders one card per exercise. Each card has a set grid with editable inputs. */}
        {exercises.map((ex, exIdx) => (
          <div key={ex.name} className="exercise-card fade-in">
            <div className="ex-header">
              <div>
                <div className="ex-name">{ex.name}</div>
                {/* Muscle group tags */}
                <div style={{ marginTop: 3, display: "flex", gap: 6 }}>
                  {ex.muscles.map((m) => (
                    <span key={m} className="muscle-tag">
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Column headers for the set grid */}
            <div className="sets-header">
              <span>#</span>
              <span>Weight (lbs)</span>
              <span>Reps</span>
              <span>RPE</span>
            </div>

            {/* Set rows — one row per set */}
            {ex.sets.map((s, setIdx) => {
              // A set is "empty" if both weight and reps are blank (not yet logged)
              const empty = !s.weight && !s.reps;
              return (
                <div key={setIdx} className="set-row">
                  {/* Set number bubble — grey if not yet completed */}
                  <div className={`set-num${empty ? " empty" : ""}`}>
                    {setIdx + 1}
                  </div>

                  {/* Controlled inputs — each change calls updateSet */}
                  <input
                    className="set-input"
                    value={s.weight}
                    placeholder="—"
                    onChange={(e) =>
                      updateSet(exIdx, setIdx, "weight", e.target.value)
                    }
                  />
                  <input
                    className="set-input"
                    value={s.reps}
                    placeholder="—"
                    onChange={(e) =>
                      updateSet(exIdx, setIdx, "reps", e.target.value)
                    }
                  />
                  <input
                    className="set-input"
                    value={s.rpe}
                    placeholder="—"
                    onChange={(e) =>
                      updateSet(exIdx, setIdx, "rpe", e.target.value)
                    }
                  />
                </div>
              );
            })}

            {/* Previous session stats shown for reference */}
            <div className="prev-stats">{ex.prev}</div>
          </div>
        ))}

        {/* ── Footer actions ── */}
        <div
          style={{
            padding: "0 16px",
            display: "flex",
            gap: 10,
            marginBottom: 14,
          }}
        >
          {/* TODO: Open exercise search modal → GET /exercise-search/search?name= */}
          <button
            className="btn btn-ghost"
            style={{ flex: 1 }}
            onClick={addExercise}
          >
            + Add Exercise
          </button>
          {/* Opens the post-workout summary modal */}
          <button
            className="btn btn-green"
            style={{ flex: 1 }}
            onClick={() => setShowModal(true)}
          >
            Finish Workout
          </button>
        </div>
      </div>

      {/* Modal only renders when showModal is true */}
      {showModal && <WorkoutModal onClose={handleModalClose} />}
    </div>
  );
}
