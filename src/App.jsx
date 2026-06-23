import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Navbar from './components/Navbar'
import LensOnboarding from './components/LensOnboarding'
import Dashboard from './pages/Dashboard'
import LearnPage from './pages/LearnPage'
import QuizPage from './pages/QuizPage'
import TutorPage from './pages/TutorPage'
import MapPage from './pages/MapPage'
import ReflectionPage from './pages/ReflectionPage'
import ObservePage from './pages/ObservePage'
import CasesPage from './pages/CasesPage'
import CastingPage from './pages/CastingPage'
import CastingHistoryPage from './pages/CastingHistoryPage'
import { useStore } from './store'

export default function App() {
  const { darkMode, loadLens, lensReady, lensChosen } = useStore()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  useEffect(() => {
    loadLens()
  }, [loadLens])

  return (
    <BrowserRouter>
      <div className="min-h-screen transition-colors duration-200">
        <Navbar />
        <main className="pb-16">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/learn/:day" element={<LearnPage />} />
            <Route path="/quiz/:day" element={<QuizPage />} />
            <Route path="/tutor" element={<TutorPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/reflection" element={<ReflectionPage />} />
            <Route path="/observe" element={<ObservePage />} />
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/casting" element={<CastingPage />} />
            <Route path="/casting-history" element={<CastingHistoryPage />} />
          </Routes>
        </main>
        {lensReady && !lensChosen && <LensOnboarding />}
      </div>
    </BrowserRouter>
  )
}
