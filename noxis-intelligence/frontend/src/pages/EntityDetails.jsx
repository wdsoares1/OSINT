import React from 'react'
import { useParams } from 'react-router-dom'
import Sidebar from '../components/Sidebar'

export default function EntityDetails() {
  const { id } = useParams()

  return (
    <div className="flex h-screen bg-noxis-darker overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        <h1 className="text-3xl font-bold text-white mb-2">Detalhes da Entidade</h1>
        <p className="text-white/40">ID: {id}</p>
        <div className="mt-8 text-white/60">
          Página em desenvolvimento...
        </div>
      </main>
    </div>
  )
}
