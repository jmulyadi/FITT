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

import { useState } from 'react'
import Login      from './pages/Login'
import Dashboard  from './pages/Dashboard'
import Workout    from './pages/Workout'
import Nutrition  from './pages/Nutrition'
import Recovery   from './pages/Recovery'
import Progress   from './pages/Progress'
import Chat       from './pages/Chat'
import BottomNav  from './components/BottomNav'

export default function App() {
  // `page` holds the name of the currently visible page (matches page file names)
  const [page, setPage] = useState('login')

  return (
    // app-shell caps the layout at 420px wide and centers it — mobile-first design
    <div className="app-shell">

      {/* Only the active page renders — inactive pages are fully unmounted */}
      {page === 'login'     && <Login     goTo={setPage} />}
      {page === 'dashboard' && <Dashboard goTo={setPage} />}
      {page === 'workout'   && <Workout   goTo={setPage} />}
      {page === 'nutrition' && <Nutrition goTo={setPage} />}
      {page === 'recovery'  && <Recovery  goTo={setPage} />}
      {page === 'progress'  && <Progress  goTo={setPage} />}
      {page === 'chat'      && <Chat      goTo={setPage} />}

      {/* BottomNav is always visible except on the login screen */}
      {page !== 'login' && <BottomNav page={page} goTo={setPage} />}
    </div>
  )
}
