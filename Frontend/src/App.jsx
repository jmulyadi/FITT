// ─────────────────────────────────────────────────────────────────────────────
// App.jsx — Root component and page router
//
// This app uses simple state-based navigation instead of React Router.
// The `page` state string controls which page is visible. Passing `setPage`
// down as `goTo` lets any child component trigger a page change.
//
// Navigation flow:
//   Login → sets page to 'dashboard' on button click
//   All other pages → BottomNav calls goTo() with the destination page name
//
// NOTE: BottomNav is hidden on the login page (user hasn't signed in yet).
// ─────────────────────────────────────────────────────────────────────────────

import { useState } from "react";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Workout from "./pages/Workout";
import Nutrition from "./pages/Nutrition";
import Recovery from "./pages/Recovery";
import Progress from "./pages/Progress";
import Chat from "./pages/Chat";
import BottomNav from "./components/BottomNav";
import Signup from "./pages/Signup";

export default function App() {
  const [page, setPage] = useState("login");

  const authPages = ["login", "signup"];

  return (
    <div className="app-shell">
      {page === "login" && <Login goTo={setPage} />}
      {page === "signup" && <Signup goTo={setPage} />}

      {page === "dashboard" && <Dashboard goTo={setPage} />}
      {page === "workout" && <Workout goTo={setPage} />}
      {page === "nutrition" && <Nutrition goTo={setPage} />}
      {page === "recovery" && <Recovery goTo={setPage} />}
      {page === "progress" && <Progress goTo={setPage} />}
      {page === "chat" && <Chat goTo={setPage} />}

      {!authPages.includes(page) && <BottomNav page={page} goTo={setPage} />}
    </div>
  );
}
