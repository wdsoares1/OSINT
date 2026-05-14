import React, { useRef, useEffect } from 'react'

/**
 * GraphView - Componente para visualização de grafos de relacionamentos
 * Utiliza react-force-graph-2d para renderização interativa
 */
export default function GraphView({ data, width = 800, height = 600 }) {
  const fgRef = useRef()

  // Dados mockados para demonstração (em produção, viriam da API)
  const graphData = data || {
    nodes: [
      { id: '1', name: 'João da Silva', risk: 72 },
      { id: '2', name: 'Maria Santos', risk: 45 },
      { id: '3', name: 'Empresa XYZ', risk: 89 },
      { id: '4', name: 'Carlos Oliveira', risk: 30 },
    ],
    links: [
      { source: '1', target: '3' },
      { source: '2', target: '3' },
      { source: '1', target: '4' },
    ],
  }

  useEffect(() => {
    if (fgRef.current && graphData) {
      fgRef.current.graphData(graphData)
    }
  }, [graphData])

  return (
    <div className="bg-noxis-dark rounded-lg p-6 tactical-border">
      <h3 className="text-lg font-bold text-white mb-4">Grafo de Relacionamentos</h3>
      <div 
        className="border border-noxis-blue/20 rounded-lg overflow-hidden"
        style={{ width, height }}
      >
        {/* 
          Em produção, importar e usar react-force-graph-2d:
          import ForceGraph2D from 'react-force-graph-2d'
          
          <ForceGraph2D
            ref={fgRef}
            graphData={graphData}
            nodeColor={node => getRiskColor(node.risk)}
            nodeLabel={node => node.name}
            linkColor={() => '#2563eb'}
            backgroundColor="#0a0e13"
          />
        */}
        <div className="w-full h-full flex items-center justify-center bg-noxis-darker">
          <div className="text-center">
            <p className="text-white/40 mb-2">Visualização de Grafo</p>
            <p className="text-xs text-noxis-blue">react-force-graph-2d</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function getRiskColor(risk) {
  if (risk >= 80) return '#ef4444'
  if (risk >= 60) return '#f97316'
  if (risk >= 40) return '#eab308'
  if (risk >= 20) return '#22c55e'
  return '#6b7280'
}
