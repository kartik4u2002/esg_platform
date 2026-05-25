import React from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'

const Layout: React.FC = () => {
  return (
    <div className="min-h-screen bg-surface-950">
      {/* Subtle background gradient orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-500/[0.03] rounded-full blur-3xl" />
        <div className="absolute top-1/3 -left-40 w-80 h-80 bg-violet-500/[0.03] rounded-full blur-3xl" />
        <div className="absolute -bottom-40 right-1/3 w-96 h-96 bg-indigo-500/[0.02] rounded-full blur-3xl" />
      </div>

      <Navbar />

      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
