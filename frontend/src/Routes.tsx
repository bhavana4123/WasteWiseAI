import { lazy, Suspense } from 'react'
const LandingPage = lazy(() => import('./LandingPage'))
const Simulation = lazy(() => import('./App'))

// Native links preserve browser history, refresh, and modifier-click behavior.
// The static host must fall back to index.html for /simulation (see README).
export default function Routes() {
  const path = window.location.pathname.replace(/\/$/, '') || '/'
  if (path === '/simulation') return <Suspense fallback={<div className="route-loading" role="status">Preparing WasteWise…</div>}><Simulation /></Suspense>
  if (path === '/') return <Suspense fallback={<div className="route-loading" role="status">Preparing WasteWise…</div>}><LandingPage /></Suspense>
  return <div className="route-loading"><h1>Page not found</h1><a href="/">Return to WasteWise</a></div>
}
