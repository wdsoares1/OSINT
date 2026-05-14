import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import RiskGauge from '../components/RiskGauge'
import EntityCard from '../components/EntityCard'
import { searchService, entityService } from '../services/api'
import { Search, AlertTriangle, Users, FileText, Activity, TrendingUp } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalEntities: 0,
    activeCases: 0,
    criticalRisk: 0,
    searchesToday: 0,
  })
  const [recentEntities, setRecentEntities] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  async function loadDashboardData() {
    try {
      // Em produção, buscar dados reais da API
      // const [entitiesData, casesData] = await Promise.all([
      //   entityService.getAll({ limit: 5 }),
      //   caseService.getAll({ status: 'OPEN' }),
      // ])
      
      // Dados mockados para demonstração
      setStats({
        totalEntities: 127,
        activeCases: 23,
        criticalRisk: 8,
        searchesToday: 45,
      })

      setRecentEntities([
        {
          id: 1,
          name: 'João da Silva',
          entity_type: 'PERSON',
          document: '123.456.789-00',
          document_type: 'CPF',
          risk_level: 'HIGH',
          risk_score: 72,
          status: 'ACTIVE',
          findings_count: 15,
          sources_count: 4,
          cases_count: 2,
          tags: ['Investigação', 'Prioritário'],
        },
        {
          id: 2,
          name: 'Maria Santos',
          entity_type: 'PERSON',
          document: '987.654.321-00',
          document_type: 'CPF',
          risk_level: 'MEDIUM',
          risk_score: 45,
          status: 'ACTIVE',
          findings_count: 8,
          sources_count: 3,
          cases_count: 1,
          tags: ['Monitoramento'],
        },
        {
          id: 3,
          name: 'Empresa XYZ Ltda',
          entity_type: 'COMPANY',
          document: '12.345.678/0001-00',
          document_type: 'CNPJ',
          risk_level: 'CRITICAL',
          risk_score: 89,
          status: 'ACTIVE',
          findings_count: 32,
          sources_count: 6,
          cases_count: 3,
          tags: ['Corrupção', 'Fraude', 'Urgente'],
        },
      ])
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen bg-noxis-darker">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-noxis-blue">
            <Activity className="w-12 h-12 animate-spin mx-auto mb-4" />
            <p className="text-white/60">Carregando NOXIS Intelligence...</p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-noxis-darker overflow-hidden">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto p-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-white/40">Visão geral das operações de inteligência</p>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={Users}
            label="Entidades"
            value={stats.totalEntities}
            color="text-blue-500"
          />
          <StatCard
            icon={FileText}
            label="Casos Ativos"
            value={stats.activeCases}
            color="text-green-500"
          />
          <StatCard
            icon={AlertTriangle}
            label="Risco Crítico"
            value={stats.criticalRisk}
            color="text-red-500"
          />
          <StatCard
            icon={Search}
            label="Buscas Hoje"
            value={stats.searchesToday}
            color="text-purple-500"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Risk Overview */}
          <div className="lg:col-span-1 bg-noxis-dark rounded-lg p-6 tactical-border">
            <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp size={20} className="text-noxis-blue" />
              Distribuição de Risco
            </h2>
            
            <div className="space-y-6">
              <div className="text-center">
                <RiskGauge score={(stats.criticalRisk / stats.totalEntities) * 100} size="large" />
              </div>
              
              <div className="space-y-3">
                <RiskBar level="CRITICAL" count={stats.criticalRisk} color="red" />
                <RiskBar level="HIGH" count={35} color="orange" />
                <RiskBar level="MEDIUM" count={52} color="yellow" />
                <RiskBar level="LOW" count={32} color="green" />
              </div>
            </div>
          </div>

          {/* Recent Entities */}
          <div className="lg:col-span-2 bg-noxis-dark rounded-lg p-6 tactical-border">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Activity size={20} className="text-noxis-blue" />
                Entidades Recentes
              </h2>
              <Link to="/entities" className="text-noxis-blue text-sm hover:underline">
                Ver todas →
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentEntities.map((entity) => (
                <EntityCard key={entity.id} entity={entity} />
              ))}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-noxis-dark rounded-lg p-6 tactical-border">
          <h2 className="text-lg font-bold text-white mb-4">Ações Rápidas</h2>
          <div className="flex gap-4">
            <Link
              to="/search"
              className="flex-1 bg-noxis-blue hover:bg-blue-600 text-white py-4 px-6 rounded-lg font-bold transition-all duration-200 flex items-center justify-center gap-3 tactical-pulse"
            >
              <Search size={20} />
              Nova Investigação
            </Link>
            <button className="flex-1 bg-noxis-blue/20 hover:bg-noxis-blue/30 text-noxis-blue py-4 px-6 rounded-lg font-bold transition-all duration-200 border border-noxis-blue/30">
              Exportar Relatório
            </button>
            <button className="flex-1 bg-noxis-blue/20 hover:bg-noxis-blue/30 text-noxis-blue py-4 px-6 rounded-lg font-bold transition-all duration-200 border border-noxis-blue/30">
              Ver Auditoria
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-noxis-dark rounded-lg p-6 tactical-border">
      <div className="flex items-center justify-between mb-4">
        <Icon size={24} className={color} />
        <span className={`text-3xl font-bold ${color}`}>{value}</span>
      </div>
      <p className="text-white/60 text-sm">{label}</p>
    </div>
  )
}

function RiskBar({ level, count, color }) {
  const colors = {
    red: 'bg-red-500',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    green: 'bg-green-500',
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-white/40 w-16">{level}</span>
      <div className="flex-1 h-2 bg-noxis-darker rounded-full overflow-hidden">
        <div className={`h-full ${colors[color]} rounded-full`} style={{ width: `${Math.min(count, 100)}%` }}></div>
      </div>
      <span className="text-xs text-white/60 w-8 text-right">{count}</span>
    </div>
  )
}
