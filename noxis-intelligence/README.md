# NOXIS Intelligence Platform

Plataforma automatizada de OSINT e investigação tática para órgãos de controle e corregedoria.

## 🚀 Visão Geral

NOXIS Intelligence é uma solução completa de inteligência que integra múltiplas fontes de dados abertos (OSINT) para investigação rápida e eficiente. A plataforma realiza buscas paralelas em:

- **Google Dorks**: Buscas automatizadas com técnicas avançadas
- **Portal da Transparência**: Dados governamentais de despesas e servidores
- **BNMP/CNJ**: Banco Nacional de Mandados de Prisão
- **Redes Sociais**: Monitoramento de menções em Surface Web

## 🏗️ Arquitetura

```
noxis-intelligence/
├── backend/                 # API FastAPI (Python)
│   ├── app/
│   │   ├── core/           # Configurações e database
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── routers/        # Endpoints da API
│   │   ├── scrapers/       # Engine de scraping modular
│   │   ├── services/       # Serviços de negócio (OSINT, Graph, Report)
│   │   ├── middleware/     # Middleware de auditoria
│   │   ├── templates/      # Templates HTML
│   │   └── main.py         # Entry point
│   ├── requirements.txt
│   └── .env.example
└── frontend/               # React + Vite (Tailwind CSS)
    ├── src/
    │   ├── components/     # Componentes reutilizáveis
    │   ├── pages/          # Páginas da aplicação
    │   └── App.jsx
    └── package.json
```

## 📦 Instalação

### Backend

```bash
cd backend

# Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Instalar browsers do Playwright
playwright install chromium

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Rodar migrações do banco (se necessário)
# python -m alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev
```

## 🔧 Variáveis de Ambiente

```bash
# Database
DATABASE_URL=postgresql://noxis:noxis_pass@localhost:5432/noxis_db

# Security
SECRET_KEY=sua-chave-secreta-aqui

# Application
DEBUG=true
LOG_LEVEL=INFO

# Scraping
HEADLESS_BROWSER=true
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

## 📡 API Endpoints

### POST `/api/v1/search`

Realiza busca OSINT completa em múltiplas fontes.

**Request:**
```json
{
  "query": "12345678900",
  "query_type": "CPF",
  "sources": ["google_dorks", "portal_transparencia", "bnmp", "social_media"],
  "include_details": true
}
```

**Headers:**
- `X-Operator-ID`: ID do operador (obrigatório para auditoria)
- `X-Operator-Name`: Nome do operador

**Response:**
```json
{
  "query": "12345678900",
  "query_type": "CPF",
  "status": "success",
  "sources_consulted": ["google_dorks", "bnmp"],
  "results": { ... },
  "summary": {
    "total_findings": 15,
    "has_critical_findings": false,
    "risk_score": 35.5,
    "risk_level": "MEDIUM"
  },
  "audit_log_id": 1
}
```

### GET `/health`

Verificação de saúde da API.

## 🔍 Scrapers Modulares

A plataforma utiliza uma arquitetura de scrapers modulares com:

- **Rotação de User-Agents**: Evita bloqueios por rate limiting
- **Retry Automático**: Tenta novamente em caso de falha
- **Timeout Configurável**: Previne requisições travadas
- **Normalização de Dados**: Padroniza saída em JSON
- **Suporte Playwright**: Para páginas JavaScript-heavy

### Criando Novo Scraper

```python
from app.scrapers.base_scraper import BaseScraper

class MeuScraper(BaseScraper):
    def __init__(self):
        super().__init__(name="MeuScraper")
    
    async def scrape(self, query: str, **kwargs) -> Dict[str, Any]:
        # Implementar lógica de scraping
        return self.normalize_data({"dados": "aqui"})
```

## 🛡️ Segurança e Auditoria

Todas as consultas são registradas no banco de dados com:

- Timestamp exato
- ID e nome do operador
- Tipo de ação e identificador buscado
- Fontes consultadas
- IP address e User-Agent
- Duração da consulta
- Status e resultados resumidos

## 📊 Funcionalidades

- ✅ Busca multi-fonte paralela
- ✅ Classificação automática de risco
- ✅ Geração de grafos de relacionamento
- ✅ Relatórios executivos em HTML/PDF
- ✅ Exportação JSON/GEXF/CSV
- ✅ Logs de auditoria completos
- ✅ Interface tática dark mode

## 🧪 Testes

```bash
cd backend
pytest tests/ -v
```

## 📄 Licença

Uso restrito a órgãos de controle e corregedoria.

---

**NOXIS Intelligence Platform v1.0.0**
