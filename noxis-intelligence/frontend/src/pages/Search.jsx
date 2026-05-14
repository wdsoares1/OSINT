import React, { useState } from 'react'
import Sidebar from '../components/Sidebar'
import RiskGauge from '../components/RiskGauge'
import { searchService } from '../services/api'
import { Search, Shield, Globe, Building, User, AlertTriangle, CheckCircle, Loader } from 'lucide-react'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [selectedSources, setSelectedSources] = useState({
    google_dorks: true,
    portal_transparencia: true,
    bnmp: true,
    social_media: true,
  })

  async function handleSearch(e) {
    e.preventDefault()
    
    if (!query.trim()) return
    
    setLoading(true)
    setError(null)
    setResults(null)
    
    try {
      const sources = Object.entries(selectedSources)
        .filter(([_, enabled]) => enabled)
        .map(([name]) => name)
      
      const data = await searchService.search(query, {
        sources: sources.length > 0 ? sources : null,
      })
      
      setResults(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao realizar busca')
    } finally {
      setLoading(false)
    }
  }

  function toggleSource(source) {
    setSelectedSources(prev => ({
      ...prev,
      [source]: !prev[source],
    }))
  }

  return (
    <div className="flex h-screen bg-noxis-darker overflow-hidden">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto p-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Investigar</h1>
          <p className="text-white/40">Busca OSINT multi-fonte automatizada</p>
        </header>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="bg-noxis-dark rounded-lg p-6 tactical-border">
            <div className="flex gap-4 mb-6">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" size={20} />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="CPF, Nome ou CNPJ..."
                  className="w-full bg-noxis-darker border border-noxis-blue/30 rounded-lg py-4 pl-12 pr-4 text-white placeholder:text-white/30 focus:outline-none focus:border-noxis-blue transition-colors"
                />
              </div>
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="bg-noxis-blue hover:bg-blue-600 disabled:bg-noxis-blue/50 text-white px-8 py-4 rounded-lg font-bold transition-all duration-200 flex items-center gap-2 tactical-pulse"
              >
                {loading ? <Loader className="animate-spin" size={20} /> : <Search size={20} />}
                {loading ? 'Buscando...' : 'Investigar'}
              </button>
            </div>

            {/* Source Selection */}
            <div className="flex gap-4 flex-wrap">
              <SourceToggle
                icon={Globe}
                label="Google Dorks"
                enabled={selectedSources.google_dorks}
                onToggle={() => toggleSource('google_dorks')}
              />
              <SourceToggle
                icon={Building}
                label="Portal Transparência"
                enabled={selectedSources.portal_transparencia}
                onToggle={() => toggleSource('portal_transparencia')}
              />
              <SourceToggle
                icon={Shield}
                label="BNMP/CNJ"
                enabled={selectedSources.bnmp}
                onToggle={() => toggleSource('bnmp')}
              />
              <SourceToggle
                icon={User}
                label="Redes Sociais"
                enabled={selectedSources.social_media}
                onToggle={() => toggleSource('social_media')}
              />
            </div>
          </div>
        </form>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <Loader className="w-16 h-16 animate-spin mx-auto mb-4 text-noxis-blue" />
            <p className="text-white/60">Consultando fontes de inteligência...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-red-500">
            <AlertTriangle className="inline mr-2" />
            {error}
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1 bg-noxis-dark rounded-lg p-6 tactical-border">
                <h3 className="text-lg font-bold text-white mb-4">Score de Risco</h3>
                <RiskGauge score={results.summary?.risk_score || 0} size="large" />
                
                {results.summary?.risk_indicators?.length > 0 && (
                  <div className="mt-6 space-y-2">
                    <h4 className="text-sm font-bold text-white/60">Indicadores:</h4>
                    {results.summary.risk_indicators.map((indicator, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-orange-500">
                        <AlertTriangle size={14} className="mt-0.5" />
                        {indicator}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="lg:col-span-2 bg-noxis-dark rounded-lg p-6 tactical-border">
                <h3 className="text-lg font-bold text-white mb-4">Resumo da Busca</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <SummaryStat label="Query" value={results.query_type} />
                  <SummaryStat label="Status" value={results.status} color={getStatusColor(results.status)} />
                  <SummaryStat label="Fontes" value={results.sources_consulted?.length || 0} />
                  <SummaryStat label="Achados" value={results.summary?.total_findings || 0} />
                </div>
                
                <div className="mt-6 pt-6 border-t border-noxis-blue/10">
                  <h4 className="text-sm font-bold text-white/60 mb-3">Fontes Consultadas:</h4>
                  <div className="flex gap-2 flex-wrap">
                    {results.sources_consulted?.map((source, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-noxis-blue/10 text-noxis-blue text-xs rounded-full border border-noxis-blue/30"
                      >
                        {formatSourceName(source)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Detailed Results by Source */}
            {results.results && Object.entries(results.results).map(([source, data]) => (
              <div key={source} className="bg-noxis-dark rounded-lg p-6 tactical-border">
                <h3 className="text-lg font-bold text-white mb-4 capitalize">
                  {formatSourceName(source)}
                </h3>
                {data.error ? (
                  <p className="text-red-500 text-sm">{data.error}</p>
                ) : (
                  <pre className="bg-noxis-darker rounded p-4 text-xs text-white/60 overflow-x-auto max-h-96">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

function SourceToggle({ icon: Icon, label, enabled, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-200 ${
        enabled
          ? 'bg-noxis-blue/20 border-noxis-blue/50 text-noxis-blue'
          : 'bg-noxis-darker border-noxis-blue/20 text-white/40 hover:text-white'
      }`}
    >
      <Icon size={16} />
      <span className="text-sm font-medium">{label}</span>
      {enabled && <CheckCircle size={14} className="text-noxis-blue" />}
    </button>
  )
}

function SummaryStat({ label, value, color = 'text-white' }) {
  return (
    <div>
      <div className="text-xs text-white/40 mb-1">{label}</div>
      <div className={`text-xl font-bold ${color}`}>{value}</div>
    </div>
  )
}

function getStatusColor(status) {
  switch (status) {
    case 'success': return 'text-green-500'
    case 'partial': return 'text-yellow-500'
    case 'error': return 'text-red-500'
    default: return 'text-white'
  }
}

function formatSourceName(name) {
  const names = {
    google_dorks: 'Google Dorks',
    portal_transparencia: 'Portal da Transparência',
    bnmp: 'BNMP/CNJ',
    social_media: 'Redes Sociais',
  }
  return names[name] || name
}
