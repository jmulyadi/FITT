// ─────────────────────────────────────────────────────────────────────────────
// Login.jsx — Landing / login page
//
// The first screen users see. Contains the FITT branding and a login form.
// Currently both buttons bypass auth and navigate straight to the dashboard.
//
// Props:
//   goTo — navigation function from App.jsx
//
// TODO: When backend is connected, the "Log In" button should:
//   1. POST { email, password } to /auth/signin
//   2. Store the returned access_token + refresh_token (localStorage or context)
//   3. Only then call goTo('dashboard')
//   The "Create Account" button should navigate to an onboarding/signup flow
//   and POST to /auth/signup.
// ─────────────────────────────────────────────────────────────────────────────

export default function Login({ goTo }) {
  return (
    // #page-login has a radial blue gradient background defined in index.css
    <div id="page-login" className="page" style={{ paddingTop: 60 }}>

      {/* App logo and tagline — centered in the upper half of the screen */}
      <div className="logo-area fade-in">
        <div className="logo-mark">F</div>
        <h1>FITT</h1>
        <p>Train smarter. Recover better.<br />Progress faster.</p>
      </div>

      {/* Login form — pinned to the bottom of the screen */}
      <div className="login-form fade-in">
        {/* defaultValue pre-fills the demo account for easy testing */}
        <input type="email" placeholder="Email address" defaultValue="dylan@example.com" />
        <input type="password" placeholder="Password" defaultValue="password123" />

        {/* TODO: Replace onClick with real auth call */}
        <button
          className="btn btn-primary btn-full"
          style={{ fontSize: 16, padding: 15 }}
          onClick={() => goTo('dashboard')}
        >
          Log In
        </button>

        <div className="divider">— or —</div>

        {/* TODO: Navigate to onboarding/signup flow instead of dashboard */}
        <button className="btn btn-ghost btn-full" onClick={() => goTo('dashboard')}>
          Create Account
        </button>
      </div>
    </div>
  )
}
