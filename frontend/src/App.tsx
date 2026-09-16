import { Route, Routes } from 'react-router-dom'
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

export default function App() {
  return (
    <Routes>
      <Route path="/about" element={<SplashPage />} />
      <Route path="/" element={<Layout><WorkbenchPage /></Layout>} />
      <Route path="/specs/:specId" element={<Layout><SpecPage /></Layout>} />
    </Routes>
  )
}
