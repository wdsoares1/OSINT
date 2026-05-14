import React from 'react'
import { Link } from 'react-router-dom'
import { User, Building, Shield, AlertTriangle, CheckCircle } from 'lucide-react'
import RiskGauge from './RiskGauge'

export default function EntityCard({ entity }) {
  const Icon = entity.entity_type === 'COMPANY' ? Building : User
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'ACTIVE': return 'text-green-500 bg-green-500/10'
      case 'ARCHIVED': return 'text-gray-500 bg-gray-500/10'
      case 'CLOSED': return 'text-blue-500 bg-blue-500/10'
      default: return 'text-white/60 bg-white/5'
    }
  }

  const getRiskColor = (level) => {
    switch (level) {
      case 'CRITICAL': return 'text-red-500 border-red-500/30'
      case 'HIGH': return 'text-orange-500 border-orange-500/30'
      case 'MEDIUM': return 'text-yellow-500 border-yellow-500/30'
      case 'LOW': return 'text-green-500 border-green-500/30'
      default: return 'text-gray-500 border-gray-500/30'
    }
  }

  return (
    <Link to={`/entity/${entity.id}`}>
      <div className={`bg-noxis-dark rounded-lg p-4 tactical-border hover:border-noxis-blue/50 transition-all duration-200 ${getRiskColor(entity.risk_level)}`}>
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-noxis-blue/20 flex items-center justify-center text-noxis-blue">
              <Icon size={20} />
            </div>
            <div>
              <h3 className="font-bold text-white truncate max-w-[200px]">
                {entity.name}
              </h3>
              <p className="text-xs text-white/40 font-mono">
                {entity.document_type}: {entity.document || 'N/A'}
              </p>
            </div>
          </div>
          
          <div className={`px-2 py-1 rounded text-xs font-bold ${getStatusColor(entity.status)}`}>
            {entity.status}
          </div>
        </div>

        {/* Risk Score */}
        <div className="flex items-center justify-between mb-4">
          <RiskGauge score={entity.risk_score} size="small" />
          
          <div className="text-right">
            <div className="text-xs text-white/40 mb-1">RISCO</div>
            <div className={`text-lg font-bold ${getRiskColor(entity.risk_level).split(' ')[0]}`}>
              {entity.risk_level}
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 pt-3 border-t border-noxis-blue/10">
          <div className="text-center">
            <div className="text-lg font-bold text-white">
              {entity.findings_count || 0}
            </div>
            <div className="text-xs text-white/40">Achados</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-white">
              {entity.sources_count || 0}
            </div>
            <div className="text-xs text-white/40">Fontes</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-white">
              {entity.cases_count || 0}
            </div>
            <div className="text-xs text-white/40">Casos</div>
          </div>
        </div>

        {/* Tags */}
        {entity.tags && entity.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {entity.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="px-2 py-0.5 bg-noxis-blue/10 text-noxis-blue text-xs rounded"
              >
                {tag}
              </span>
            ))}
            {entity.tags.length > 3 && (
              <span className="px-2 py-0.5 text-white/40 text-xs">
                +{entity.tags.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </Link>
  )
}
