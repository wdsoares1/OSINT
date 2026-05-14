import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Search from './pages/Search'
import EntityDetails from './pages/EntityDetails'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/search" element={<Search />} />
        <Route path="/entity/:id" element={<EntityDetails />} />
      </Routes>
    </Router>
  )
}

export default App
