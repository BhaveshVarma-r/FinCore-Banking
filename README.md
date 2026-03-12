# FinCore Banking Assistant

An agentic banking assistant powered by Gemini AI and LangGraph. This system provides intelligent, multi-agent orchestration for comprehensive banking operations including accounts, loans, fraud detection, and compliance management.

## 🚀 Features

### Core Capabilities
- **Account Management**: Balance inquiries, transaction history, fund transfers
- **Loan Processing**: Loan applications, credit scoring, repayment schedules
- **Fraud Detection**: Transaction analysis, risk profiling, suspicious activity detection
- **Compliance**: KYC verification, AML checks, regulatory compliance reporting

### Technical Highlights
- **Multi-Agent Architecture**: Specialized agents for different banking domains
- **LangGraph Orchestration**: State-based graph workflow for complex operations
- **MCP Servers**: Model Context Protocol servers for modular service implementation
- **Knowledge Graph**: Neo4j Aura integration for relationship and pattern analysis
- **Real-time Audit Trail**: Comprehensive logging of all operations
- **Modern Frontend**: Next.js + Tailwind CSS with responsive design

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+
- SQLite (for data persistence and audit logging)
- Neo4j Aura (For knowledge graph features)

## 🔧 Setup

### 1. Clone or Extract the Project
```bash
cd fincore-banking-assistant
```

### 2. Run the Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Create a Python virtual environment
- Install all Python dependencies
- Configure Unicode support
- Generate mock data for testing
- Create necessary directories

### 3. Manual Setup (Alternative)

**Backend Setup:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

```

**Frontend Setup:**
```bash
cd frontend
npm install
```

## 📦 Environment Configuration

Create or update the `.env` file in the root directory:

```env
# Database Configuration
# No Postgres required - using SQLite (fincore_audit.db)
NEO4J_URI=neo4j+s://<your-aura-db-id>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-password>

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# MCP Server Configuration
CORE_BANKING_SERVER_HOST=localhost
CORE_BANKING_SERVER_PORT=5001
CREDIT_SERVER_HOST=localhost
CREDIT_SERVER_PORT=5002
FRAUD_SERVER_HOST=localhost
FRAUD_SERVER_PORT=5003
COMPLIANCE_SERVER_HOST=localhost
COMPLIANCE_SERVER_PORT=5004

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/fincore.log

# Environment
ENVIRONMENT=development
DEBUG=true
```

## 🚀 Running the Application

### Start Backend Server
```bash
# Activate virtual environment
source venv/bin/activate

# Run FastAPI server with hot reload
python -m uvicorn src.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Start Frontend Server
```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
fincore-banking-assistant/
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
├── setup.sh                      # Setup script
├── fix_unicode.py               # Unicode configuration
├── README.md                    # This file
│
├── data/
│   └── generate_mock_data.py    # Mock data generator
│
├── src/
│   ├── main.py                  # FastAPI entry point
│   ├── database/                # Database layer
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── database.py          # DB connection & init
│   │   └── audit_service.py     # Audit logging
│   │
│   ├── mcp_servers/             # MCP server implementations
│   │   ├── core_banking_server.py
│   │   ├── credit_server.py
│   │   ├── fraud_server.py
│   │   └── compliance_server.py
│   │
│   ├── mcp_client/              # MCP client implementations
│   │   ├── client_manager.py
│   │   ├── core_banking_client.py
│   │   ├── credit_client.py
│   │   ├── fraud_client.py
│   │   └── compliance_client.py
│   │
│   ├── knowledge_graph/         # Neo4j integration
│   │   ├── kg_client.py
│   │   ├── kg_queries.py
│   │   └── seed_data.py
│   │
│   ├── agents/                  # LangGraph agents
│   │   ├── base_agent.py
│   │   ├── planner_agent.py
│   │   ├── router_agent.py
│   │   ├── account_agent.py
│   │   ├── loan_agent.py
│   │   ├── fraud_agent.py
│   │   ├── compliance_agent.py
│   │   ├── aggregator_agent.py
│   │   └── critique_agent.py
│   │
│   ├── graph/                   # Workflow orchestration
│   │   ├── state.py
│   │   └── banking_graph.py
│   │
│   └── utils/                   # Utilities
│       ├── logger.py
│       └── helpers.py
│
├── tests/                       # Unit tests
│   ├── test_core_banking_tools.py
│   ├── test_credit_tools.py
│   ├── test_fraud_tools.py
│   └── test_compliance_tools.py
│
└── frontend/                    # Next.js frontend
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── next.config.js
    ├── postcss.config.js
    ├── .env.local
    └── app/
        ├── layout.tsx
        ├── page.tsx
        ├── globals.css
        ├── components/
        │   ├── MessageBubble.tsx
        │   ├── AgentBadges.tsx
        │   ├── MetadataPanel.tsx
        │   ├── AuditTrail.tsx
        │   ├── Sidebar.tsx
        │   └── LoadingIndicator.tsx
        └── demo/
            ├── page.tsx
            └── components/
                ├── ScenarioCard.tsx
                ├── LatencyChart.tsx
                └── StatsBar.tsx
```

## 🤖 Agent Architecture

### Agents Overview

1. **Planner Agent** - Plans the sequence of operations
2. **Router Agent** - Routes requests to appropriate specialized agents
3. **Account Agent** - Manages account operations (balance, transactions, transfers)
4. **Loan Agent** - Handles loan applications and credit operations
5. **Fraud Agent** - Detects and prevents fraudulent activities
6. **Compliance Agent** - Manages KYC, AML, and regulatory compliance
7. **Aggregator Agent** - Aggregates results from multiple agents
8. **Critique Agent** - Validates and critiques results

### Workflow

```
User Query
    ↓
Router Agent (Determine route)
    ↓
Planner Agent (Create execution plan)
    ↓
Specialized Agent (Execute operation)
    ↓
Aggregator Agent (Combine results)
    ↓
Critique Agent (Validate results)
    ↓
Response to User
```

## 🗄️ Database Models

### Account
- account_id (unique)
- customer_id
- account_type (Savings, Checking, Money Market)
- balance
- currency
- status
- created_at

### Transaction
- transaction_id (unique)
- account_id
- amount
- type (Debit/Credit)
- merchant
- timestamp
- status

### Loan
- loan_id (unique)
- customer_id
- loan_type
- amount
- interest_rate
- term_months
- status
- created_at

### AuditLog
- action
- resource_type
- resource_id
- user_id
- details
- timestamp

## 🧪 Testing

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Suite
```bash
pytest tests/test_core_banking_tools.py
pytest tests/test_credit_tools.py
pytest tests/test_fraud_tools.py
pytest tests/test_compliance_tools.py
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## 📊 Mock Data

Generate mock data for testing:
```bash
python data/generate_mock_data.py
```

This creates:
- `mock_accounts.json` - Sample bank accounts
- `mock_transactions.json` - Sample transactions
- `mock_loans.json` - Sample loan records

## 🔍 API Endpoints

### Health Check
```
GET /health
```

### Root
```
GET /
```

### Chat Endpoint (Planned)
```
POST /api/chat
Body: {
  "message": "Check my account balance",
  "user_id": "USER001",
  "customer_id": "CUST001"
}
```

## 🎯 Demo Scenarios

The frontend includes demo scenarios:
- **Account Inquiry** - Check account balance and recent transactions
- **Loan Application** - Apply for personal or home loan
- **Fraud Detection** - Analyze transactions for fraud risk
- **Compliance Check** - Verify KYC and AML status

## 📝 Logging

Logs are saved to `logs/fincore_YYYYMMDD.log`

Configure logging level in `.env`:
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🔐 Security Considerations

- Store sensitive credentials in `.env` (never commit)
- Use HTTPS in production
- Implement authentication/authorization
- Validate all user inputs
- Use secure database connections
- Enable audit logging for all operations

## 🚢 Deployment

### Using Docker
```bash
docker compose up --build
```

The application will be available at:
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`

### Running Services Separately
```bash
# Backend
docker build -f Dockerfile.backend -t fincore-backend .
docker run -p 8000:8000 --env-file .env fincore-backend

# Frontend
cd frontend
docker build -f Dockerfile.frontend -t fincore-frontend .
docker run -p 3000:3000 fincore-frontend
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# OR stop conflicting Docker containers
docker stop $(docker ps -q --filter "publish=8000")
docker stop $(docker ps -q --filter "publish=3000")

# Kill the process
kill -9 <PID>
```

### Database Connection Issues
- Verify DATABASE_URL in `.env`
- Check PostgreSQL/SQLite is running
- Ensure proper permissions

### Neo4j Connection Issues
- Verify NEO4J_URI (should be `neo4j+s://...` for Aura)
- Verify NEO4J_USER, NEO4J_PASSWORD
- Check Neo4j Aura console for instance status
- Review logs in `logs/`

### Frontend Not Loading
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```





