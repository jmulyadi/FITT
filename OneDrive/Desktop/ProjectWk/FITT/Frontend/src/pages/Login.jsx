import { useState } from "react";
import { login } from "../auth/auth";

export default function Login({ goTo }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    try {
      setLoading(true);
      setError(null);

      await login(email, password);

      goTo("dashboard");
    } catch (err) {
      console.error(err);
      setError("Incorrect email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div id="page-login" className="page" style={{ paddingTop: 60 }}>
      <div className="logo-area fade-in">
        <div className="logo-mark">F</div>
        <h1>FITT</h1>
        <p>
          Train smarter. Recover better.
          <br />
          Progress faster.
        </p>
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
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setError(null);
          }}
        />

        {error && <div className="form-error">{error}</div>}

        <button
          className="btn btn-primary btn-full"
          onClick={handleLogin}
          disabled={loading}
        >
          {loading ? "Logging in..." : "Log In"}
        </button>

        <div className="divider">— or —</div>

        <button
          className="btn btn-ghost btn-full"
          onClick={() => goTo("signup")}
        >
          Create Account
        </button>
      </div>
    </div>
  );
}
