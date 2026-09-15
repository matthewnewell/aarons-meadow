import { Navigate, Route, Routes, useParams } from 'react-router-dom'
import Nav from './components/Nav'
import SpecPage from './pages/SpecPage'
import SplashPage from './pages/SplashPage'
import WorkbenchPage from './pages/WorkbenchPage'
import './App.css'

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-layout">
      <Nav />
      <div className="app-layout__body">{children}</div>
    </div>
  )
}

/** Conway's Depot's own "Test drive" always appends `/about` to whatever `url` an Application
 * registered — right for every other app, whose `url` is a bare origin. A published spec's
 * `url` is already a deep link to that one spec (see backend routes/specs.py's publish), so
 * the appended `/about` lands on `/specs/:id/about` instead — this route exists just to catch
 * that and send it to the spec itself, which is already its own "what is this" page. */
function RedirectToSpec() {
  const { specId } = useParams<{ specId: string }>()
  return <Navigate to={`/specs/${specId}`} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/about" element={<SplashPage />} />
      <Route path="/" element={<Layout><WorkbenchPage /></Layout>} />
      <Route path="/specs/:specId" element={<Layout><SpecPage /></Layout>} />
      <Route path="/specs/:specId/about" element={<RedirectToSpec />} />
    </Routes>
  )
}
