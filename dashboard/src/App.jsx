import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import Overview from './pages/Overview.jsx'
import Daily from './pages/Daily.jsx'
import SalesTracker from './pages/SalesTracker.jsx'
import CRM from './pages/CRM.jsx'
import Projections from './pages/Projections.jsx'
import TeamPerformance from './pages/TeamPerformance.jsx'
import AdsBreakdown from './pages/AdsBreakdown.jsx'
import Settings from './pages/Settings.jsx'
import { colors } from './theme.js'

export default function App() {
  return (
    <BrowserRouter basename="">
      <div style={{
        display: 'flex',
        height: '100dvh',
        background: colors.bg,
        fontFamily: "'Inter', system-ui, sans-serif",
        color: colors.text,
        overflow: 'hidden',
      }}>
        <Sidebar />
        <main style={{ flex: 1, overflow: 'auto', padding: '28px 32px' }}>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/daily" element={<Daily />} />
            <Route path="/tracker" element={<SalesTracker />} />
            <Route path="/crm" element={<CRM />} />
            <Route path="/projections" element={<Projections />} />
            <Route path="/team" element={<TeamPerformance />} />
            <Route path="/ads" element={<AdsBreakdown />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
