import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Search, 
  LayoutDashboard, 
  Users, 
  FileText, 
  Settings,
  Shield,
  Activity
} from 'lucide-react'

const menuItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/search', icon: Search, label: 'Investigar' },
  { path: '/entities', icon: Users, label: 'Entidades' },
  { path: '/cases', icon: FileText, label: 'Casos' },
  { path: '/analytics', icon: Activity, label: 'Analytics' },
  { path: '/audit', icon: Shield, label: 'Auditoria' },
  { path: '/settings', icon: Settings, label: 'Configurações' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-64 bg-noxis-dark border-r border-noxis-blue/20 flex flex-col h-full">
      {/* Logo */}
      <div className="p-6 border-b border-noxis-blue/20">
        <h1 className="text-xl font-bold text-noxis-blue tracking-wider">
          NOXIS
          <span className="text-white/60 text-sm block font-normal">Intelligence</span>
        </h1>
      </div>

      {/* Menu */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-noxis-blue/20 text-noxis-blue border border-noxis-blue/30'
                  : 'text-white/60 hover:text-white hover:bg-noxis-blue/10'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* Operator Info */}
      <div className="p-4 border-t border-noxis-blue/20">
        <div className="bg-noxis-darker rounded-lg p-4 tactical-border">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-white/40">OPERADOR ONLINE</span>
          </div>
          <p className="text-sm text-white/80 font-mono">OP-001</p>
          <p className="text-xs text-white/40">Nível de Acesso: ADMIN</p>
        </div>
      </div>
    </aside>
  )
}
