# NOXIS Intelligence Platform

Plataforma automatizada de OSINT e investigação tática para órgãos de controle e corregedoria.

## Arquitetura

```
noxis-intelligence/
├── backend/                 # FastAPI (Python)
│   ├── app/
│   │   ├── core/           # Config, Database, Logging
│   │   ├── scrapers/       # Scrapers modulares
│   │   ├── routers/        # Endpoints API
│   │   ├── models/         # Modelos SQLAlchemy
│   │   └── middleware/     # Audit logging
│   └── requirements.txt
│
└── frontend/               # React + Vite + Tailwind
    ├── src/
    │   ├── components/     # Componentes reutilizáveis
    │   ├── pages/          # Páginas da aplicação
    │   └── services/       # API client
    └── package.json
```

## Funcionalidades Implementadas (Fase 1)

### Backend (FastAPI)

- **BaseScraper**: Classe base para scrapers modulares com:
  - Rotação de User-Agents
  - Tratamento de erros e retries
  - Suporte a Playwright e aiohttp
  - Normalização de dados para JSON

- **Scrapers Implementados**:
  - `GoogleDorksScraper`: Buscas automatizadas via Google Dorks
  - `PortalTransparenciaScraper`: Consulta ao Portal da Transparência
  - `BNMPScraper`: Consulta ao Banco Nacional de Mandados de Prisão (CNJ)
  - `SocialMediaScraper`: Monitoramento de redes sociais

- **Endpoint `/api/v1/search`**:
  - Busca paralela em múltiplas fontes
  - Detecção automática de tipo de query (CPF, CNPJ, Nome)
  - Geração de score de risco
  - Criação/atualização de entidades

- **Middleware de Auditoria**:
  - Log de todas as consultas no PostgreSQL
  - Registro de operador, timestamp, IP, user-agent
  - Duração e status de cada requisição

### Frontend (React)

- **Componentes**:
  - `Sidebar`: Navegação lateral tática
  - `RiskGauge`: Medidor visual de risco
  - `EntityCard`: Card de entidade investigada
  - `GraphView`: Visualização de grafos (placeholder)

- **Páginas**:
  - `Dashboard`: Visão geral com stats e entidades recentes
  - `Search`: Interface de busca multi-fonte
  - `EntityDetails`: Detalhes da entidade

## Instalação

### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Instalar browsers do Playwright
playwright install chromium

# Copiar arquivo de ambiente
cp .env.example .env

# Executar migrations (se usar Alembic)
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar dev server
npm run dev
```

## Variáveis de Ambiente

Copie `.env.example` para `.env` no backend e ajuste:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/noxis_db
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=true
```

## API Documentation

Acesse a documentação Swagger em: http://localhost:8000/docs

### Endpoint Principal

**POST /api/v1/search**

```json
{
  "query": "12345678900",
  "query_type": "CPF",
  "sources": ["google_dorks", "bnmp", "portal_transparencia"],
  "include_details": true
}
```

Headers requeridos para auditoria:
- `X-Operator-ID`: ID do operador
- `X-Operator-Name`: Nome do operador

## Tecnologias

| Área | Tecnologia |
|------|-----------|
| Backend | Python 3.10+, FastAPI, SQLAlchemy |
| Scraping | Playwright, BeautifulSoup4, aiohttp |
| Database | PostgreSQL |
| Frontend | React 18, Vite, Tailwind CSS |
| Visualização | react-force-graph-2d, Recharts |

## Licença

Uso restrito a órgãos de controle e corregedoria autorizados.
