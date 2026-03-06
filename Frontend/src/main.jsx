// ─────────────────────────────────────────────────────────────────────────────
// main.jsx — App entry point
//
// This is the first file React runs. It does three things:
//   1. Registers all Chart.js components we use globally (only needs to happen
//      once — doing it here means every page can use charts without re-registering)
//   2. Imports the global CSS (index.css) so styles are available everywhere
//   3. Mounts the root <App /> component into the <div id="root"> in index.html
// ─────────────────────────────────────────────────────────────────────────────

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale,    // x/y axis scale types
  PointElement, LineElement,     // needed for Line charts
  BarElement,                    // needed for Bar charts
  Filler,                        // fills area under Line charts
  Tooltip, Legend,               // chart UI overlays
} from 'chart.js'
import './index.css'
import App from './App.jsx'

// Register all Chart.js components once at startup
ChartJS.register(
  CategoryScale, LinearScale,
  PointElement, LineElement, BarElement,
  Filler, Tooltip, Legend
)

// Mount the React app into the #root div in index.html
// StrictMode helps catch bugs during development (no effect in production)
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)
