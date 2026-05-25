import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import UploadPage from './pages/UploadPage'
import BatchesPage from './pages/BatchesPage'
import ReviewQueuePage from './pages/ReviewQueuePage'
import RecordDetailPage from './pages/RecordDetailPage'
import AuditTrailPage from './pages/AuditTrailPage'

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/batches" element={<BatchesPage />} />
        <Route path="/review" element={<ReviewQueuePage />} />
        <Route path="/review/:id" element={<RecordDetailPage />} />
        <Route path="/audit" element={<AuditTrailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/upload" replace />} />
    </Routes>
  )
}

export default App
