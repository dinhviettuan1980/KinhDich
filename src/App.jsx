import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Navbar from './components/Navbar'
import LensOnboarding from './components/LensOnboarding'
import Dashboard from './pages/Dashboard'
import LearnPage from './pages/LearnPage'
import QuizPage from './pages/QuizPage'
import QuePage from './pages/QuePage'
import AdminUsersPage from './pages/AdminUsersPage'
import ProfilePage from './pages/ProfilePage'
import VanKhanPage from './pages/VanKhanPage'
import TutorPage from './pages/TutorPage'
import MapPage from './pages/MapPage'
import ReflectionPage from './pages/ReflectionPage'
import ObservePage from './pages/ObservePage'
import CasesPage from './pages/CasesPage'
import CastingPage from './pages/CastingPage'
import CastingHistoryPage from './pages/CastingHistoryPage'
import ChineseCharPage from './pages/ChineseCharPage'
import SearchPage from './pages/SearchPage'
import FingerCpuIntroPage from './pages/FingerCpuIntroPage'
import FingerCpuLessonPage from './pages/FingerCpuLessonPage'
import FingerCpuSimulatorPage from './pages/FingerCpuSimulatorPage'
import FingerCpuMemoryVisualizerPage from './pages/FingerCpuMemoryVisualizerPage'
import FingerCpuAlgorithmVisualizerPage from './pages/FingerCpuAlgorithmVisualizerPage'
import FingerCpuDataStructureModePage from './pages/FingerCpuDataStructureModePage'
import FingerCpuDebugModePage from './pages/FingerCpuDebugModePage'
import FingerCpuGameMemoryPage from './pages/FingerCpuGameMemoryPage'
import FingerCpuGameSpeedPage from './pages/FingerCpuGameSpeedPage'
import FingerCpuGameHexagramBuilderPage from './pages/FingerCpuGameHexagramBuilderPage'
import FingerCpuGameBinaryModePage from './pages/FingerCpuGameBinaryModePage'
import { useStore } from './store'
import { getMe } from './api'

export default function App() {
  const { darkMode, loadLens, lensReady, lensChosen, user, logout } = useStore()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  useEffect(() => {
    loadLens()
  }, [loadLens])

  // Kiểm tra token 1 lần khi app khởi động — nếu token không hợp lệ thì tự logout,
  // không check định kỳ, không timeout.
  useEffect(() => {
    if (!user) return
    getMe().catch((err) => {
      if (err.status === 401) logout()
    })
  }, []) // eslint-disable-line

  return (
    <BrowserRouter>
      <div className="min-h-screen transition-colors duration-200">
        <Navbar />
        <main className="pb-16">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/learn/:day" element={<LearnPage />} />
            <Route path="/quiz/:day" element={<QuizPage />} />
            <Route path="/que" element={<QuePage />} />
            <Route path="/que/:so" element={<QuePage />} />
            <Route path="/admin" element={<AdminUsersPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/van-khan" element={<VanKhanPage />} />
            <Route path="/van-khan/:slug" element={<VanKhanPage />} />
            <Route path="/tutor" element={<TutorPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/reflection" element={<ReflectionPage />} />
            <Route path="/observe" element={<ObservePage />} />
            <Route path="/cases" element={<CasesPage />} />
            <Route path="/casting" element={<CastingPage />} />
            <Route path="/casting-history" element={<CastingHistoryPage />} />
            <Route path="/additional/chinese" element={<ChineseCharPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/finger-cpu" element={<FingerCpuIntroPage />} />
            <Route path="/finger-cpu/bai/:id" element={<FingerCpuLessonPage />} />
            <Route path="/finger-cpu/simulator" element={<FingerCpuSimulatorPage />} />
            <Route path="/finger-cpu/memory-visualizer" element={<FingerCpuMemoryVisualizerPage />} />
            <Route path="/finger-cpu/algorithm-visualizer" element={<FingerCpuAlgorithmVisualizerPage />} />
            <Route path="/finger-cpu/data-structure-mode" element={<FingerCpuDataStructureModePage />} />
            <Route path="/finger-cpu/debug-mode" element={<FingerCpuDebugModePage />} />
            <Route path="/finger-cpu/game/ghi-nho" element={<FingerCpuGameMemoryPage />} />
            <Route path="/finger-cpu/game/toc-do" element={<FingerCpuGameSpeedPage />} />
            <Route path="/finger-cpu/game/hexagram-builder" element={<FingerCpuGameHexagramBuilderPage />} />
            <Route path="/finger-cpu/game/binary-mode" element={<FingerCpuGameBinaryModePage />} />
            <Route path="/additional/chinese/:id" element={<ChineseCharPage />} />
          </Routes>
        </main>
        {lensReady && !lensChosen && <LensOnboarding />}
      </div>
    </BrowserRouter>
  )
}
