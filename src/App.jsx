import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import LearnPage from './pages/LearnPage'
import QuizPage from './pages/QuizPage'
import TutorPage from './pages/TutorPage'
import MapPage from './pages/MapPage'
import { useStore } from './store'

export default function App() {
  const { darkMode } = useStore()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

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
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
