import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// Cria instância do axios com configuração padrão
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para adicionar headers de autenticação/auditoria
api.interceptors.request.use(
  (config) => {
    // Adiciona ID do operador (em produção, viria do contexto de auth)
    const operatorId = localStorage.getItem('operator_id') || 'OP-001'
    const operatorName = localStorage.getItem('operator_name') || 'Operador Padrão'
    
    config.headers['X-Operator-ID'] = operatorId
    config.headers['X-Operator-Name'] = operatorName
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    
    if (error.response?.status === 401) {
      // Redirect para login ou tratar sessão expirada
      console.warn('Não autorizado - verificar autenticação')
    }
    
    return Promise.reject(error)
  }
)

// Serviços de busca
export const searchService = {
  /**
   * Realiza busca OSINT completa
   * @param {string} query - CPF, Nome ou outro identificador
   * @param {Object} options - Opções adicionais
   */
  async search(query, options = {}) {
    const response = await api.post('/search', {
      query,
      query_type: options.queryType || 'AUTO',
      sources: options.sources || null,
      include_details: options.includeDetails !== false,
    })
    return response.data
  },
}

// Serviços de entidade
export const entityService = {
  async getAll(params = {}) {
    const response = await api.get('/entities', { params })
    return response.data
  },

  async getById(id) {
    const response = await api.get(`/entities/${id}`)
    return response.data
  },

  async create(data) {
    const response = await api.post('/entities', data)
    return response.data
  },

  async update(id, data) {
    const response = await api.put(`/entities/${id}`, data)
    return response.data
  },

  async delete(id) {
    const response = await api.delete(`/entities/${id}`)
    return response.data
  },
}

// Serviços de casos
export const caseService = {
  async getAll(params = {}) {
    const response = await api.get('/cases', { params })
    return response.data
  },

  async getById(id) {
    const response = await api.get(`/cases/${id}`)
    return response.data
  },

  async create(data) {
    const response = await api.post('/cases', data)
    return response.data
  },

  async update(id, data) {
    const response = await api.put(`/cases/${id}`, data)
    return response.data
  },
}

// Serviços de auditoria
export const auditService = {
  async getLogs(params = {}) {
    const response = await api.get('/audit/logs', { params })
    return response.data
  },

  async getLogById(id) {
    const response = await api.get(`/audit/logs/${id}`)
    return response.data
  },
}

// Health check
export const healthService = {
  async check() {
    const response = await api.get('/health')
    return response.data
  },
}

export default api
