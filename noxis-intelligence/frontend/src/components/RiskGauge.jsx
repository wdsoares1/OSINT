import React from 'react'

export default function RiskGauge({ score, size = 'medium' }) {
  // Normaliza score para 0-100
  const normalizedScore = Math.min(Math.max(score || 0, 0), 100)
  
  // Determina cor e nível baseado no score
  const getRiskLevel = (score) => {
    if (score >= 80) return { level: 'CRITICAL', color: 'text-red-500', bg: 'bg-red-500' }
    if (score >= 60) return { level: 'HIGH', color: 'text-orange-500', bg: 'bg-orange-500' }
    if (score >= 40) return { level: 'MEDIUM', color: 'text-yellow-500', bg: 'bg-yellow-500' }
    if (score >= 20) return { level: 'LOW', color: 'text-green-500', bg: 'bg-green-500' }
    return { level: 'UNKNOWN', color: 'text-gray-500', bg: 'bg-gray-500' }
  }

  const { level, color, bg } = getRiskLevel(normalizedScore)

  // Tamanhos
  const sizes = {
    small: { container: 'w-16 h-16', text: 'text-xs', value: 'text-lg' },
    medium: { container: 'w-24 h-24', text: 'text-sm', value: 'text-2xl' },
    large: { container: 'w-32 h-32', text: 'text-base', value: 'text-3xl' },
  }

  const currentSize = sizes[size] || sizes.medium

  // Calcula ângulo do gauge (180 graus = semicírculo)
  const angle = (normalizedScore / 100) * 180

  return (
    <div className="flex flex-col items-center">
      <div className={`relative ${currentSize.container}`}>
        {/* Fundo do gauge */}
        <svg viewBox="0 0 100 50" className="w-full h-full">
          {/* Arco de fundo */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="#1c2025"
            strokeWidth="10"
            strokeLinecap="round"
          />
          {/* Arco de progresso */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${(angle / 180) * 126} 126`}
            className={color}
          />
        </svg>

        {/* Score numérico */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pt-4">
          <span className={`font-bold ${currentSize.value} ${color}`}>
            {Math.round(normalizedScore)}
          </span>
          <span className={`text-xs text-white/40 ${currentSize.text}`}>RISCO</span>
        </div>
      </div>

      {/* Label do nível */}
      <div className={`mt-2 px-3 py-1 rounded-full text-xs font-bold tactical-border ${color.replace('text', 'bg')}/10 ${color}`}>
        {level}
      </div>
    </div>
  )
}
