import { useState } from "react";
import { createUser } from "../api/users";
import { login } from "../auth/auth";

export default function Signup({ goTo }) {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [age, setAge] = useState("");
  const [gender, setGender] = useState("other");
  const [weight, setWeight] = useState("");
  const [height, setHeight] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("beginner");

  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function calculateBMI(weight, height) {
    const h = height / 100;
    return weight / (h * h);
  }

  async function handleSignup() {
    try {
      setError(null);

      if (password !== confirmPassword) {
        setError("Passwords do not match.");
        return;
      }

      if (!age || !weight || !height) {
        setError("Please fill out all fields.");
        return;
      }

      setLoading(true);

      const bmi = calculateBMI(Number(weight), Number(height));

      const userData = {
        email,
        password,
        username,
        age: Number(age),
        gender,
        weight: Number(weight),
        height: Number(height),
        experience_level: experienceLevel,
        bmi: Number(bmi.toFixed(2)),
      };

      await createUser(userData);

      await login(email, password);

      goTo("dashboard");
    } catch (err) {
      console.error(err);
      setError("Failed to create account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div id="page-login" className="page" style={{ paddingTop: 60 }}>
      <div className="logo-area fade-in">
        <div className="logo-mark">F</div>
        <h1>Create Account</h1>
        <p>Start tracking your workouts.</p>
      </div>

      <div className="login-form fade-in">
        <input
          type="email"
          placeholder="Email address"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            setError(null);
          }}
        />

        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => {
            setUsername(e.target.value);
            setError(null);
          }}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setError(null);
          }}
        />

        <input
          type="password"
          placeholder="Confirm password"
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value);
            setError(null);
          }}
        />

        <input
          type="number"
          placeholder="Age"
          value={age}
          onChange={(e) => {
            setAge(e.target.value);
            setError(null);
          }}
        />

        <select value={gender} onChange={(e) => setGender(e.target.value)}>
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>

        <input
          type="number"
          placeholder="Weight (kg)"
          value={weight}
          onChange={(e) => {
            setWeight(e.target.value);
            setError(null);
          }}
        />

        <input
          type="number"
          placeholder="Height (cm)"
          value={height}
          onChange={(e) => {
            setHeight(e.target.value);
            setError(null);
          }}
        />

        <select
          value={experienceLevel}
          onChange={(e) => setExperienceLevel(e.target.value)}
        >
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="advanced">Advanced</option>
        </select>

        {error && <div className="form-error">{error}</div>}

        <button
          className="btn btn-primary btn-full"
          onClick={handleSignup}
          disabled={loading}
        >
          {loading ? "Creating account..." : "Create Account"}
        </button>

        <div className="divider">— or —</div>

        <button
          className="btn btn-ghost btn-full"
          onClick={() => goTo("login")}
        >
          Back to Login
        </button>
      </div>
    </div>
  );
}
