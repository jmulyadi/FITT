// ─────────────────────────────────────────────────────────────────────────────
// BottomNav.jsx — Fixed bottom navigation bar
//
// Renders 6 tab buttons at the bottom of the screen (Home, Workout, Nutrition,
// Recovery, Progress, AI Coach). The active tab is highlighted in blue.
//
// Props:
//   page  — the currently active page name (string), used to apply .active class
//   goTo  — function to call with a page name string to navigate there
//
// The nav is fixed-position so it always stays at the bottom regardless of
// scroll position. The app-shell max-width (420px) keeps it aligned with content.
// ─────────────────────────────────────────────────────────────────────────────

export default function BottomNav({ page, goTo }) {
  // Each item defines the page id, display label, and inline SVG icon
  const items = [
    {
      id: 'dashboard', label: 'Home',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
        </svg>
      ),
    },
    {
      id: 'workout', label: 'Workout',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M6.5 6.5h11M6.5 17.5h11M3 12h18M6 8.5v7M18 8.5v7"/>
        </svg>
      ),
    },
    {
      id: 'nutrition', label: 'Nutrition',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/>
        </svg>
      ),
    },
    {
      id: 'recovery', label: 'Recovery',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
        </svg>
      ),
    },
    {
      id: 'progress', label: 'Progress',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
      ),
    },
    {
      id: 'chat', label: 'AI Coach',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      ),
    },
  ]

  return (
    <nav className="bottom-nav">
      {items.map(item => (
        <button
          key={item.id}
          // Add 'active' class when this tab matches the current page
          className={`nav-item${page === item.id ? ' active' : ''}`}
          onClick={() => goTo(item.id)}
        >
          {item.icon}
          {item.label}
        </button>
      ))}
    </nav>
  )
}
