# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install backend dependencies
pip install -r backend/app/requirements.txt

# Install frontend dependencies
cd frontend && npm install

# Set up environment variables (copy from .env.example if available)
# Required: OPENAI_API_KEY, DB_* settings
```

### Database Setup
```bash
# Start PostgreSQL database only
docker-compose up -d postgres

# Check database connection
python3 -c "import psycopg2; print('Connection successful')" 2>/dev/null && echo "✅ Connected" || echo "❌ Connection failed"
```

### Full Docker Environment
```bash
# Build and start all services (database, backend, frontend)
docker-compose up -d --build

# Start all services (without rebuilding)
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Check service status
docker-compose ps

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Restart specific service
docker-compose restart backend

# Execute commands inside containers
docker exec -it tejas_backend bash
docker exec -it tejas_frontend sh
docker exec -it tejas_postgres psql -U postgres -d testdb
```

### Application Execution
```bash
# Run the main database monitoring flow (CrewAI Flow)
cd backend && python main.py

# Start the FastAPI server (default: http://0.0.0.0:8000)
cd backend && python app/start_api.py

# Start the Next.js frontend development server (http://localhost:3000)
cd frontend && npm run dev

# Build the frontend for production
cd frontend && npm run build

# Generate flow visualization
cd backend && python -c "from main import plot_flow; plot_flow()"

# Run database monitoring crew directly
cd backend && python -c "from crews.db_agent.database_agent import execute_database_monitoring; result = execute_database_monitoring(); print('Result:', result['result'])"

# Execute a long-running test query
cd backend && python long_query.py

# Run ticket analyzer crew
cd backend && python -c "from crews.ticket_analyzer.ticket_analyzer import execute_ticket_analysis; result = execute_ticket_analysis(); print('Result:', result)"

# Run database reasoning crew
cd backend && python -c "from crews.db_reasoning_crew.db_reasoning_crew import execute_database_complex; result = execute_database_complex(); print('Result:', result)"
```

### Frontend Development
```bash
# Lint frontend code
cd frontend && npm run lint

# Type checking (TypeScript)
cd frontend && npm run build

# Development server with hot reload
cd frontend && npm run dev

# Production build
cd frontend && npm run build && npm run start
```

### Database Monitoring Commands
```bash
# Check active database queries
python3 -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port='5433', database='testdb', user='postgres', password='postgres')
cur = conn.cursor()
cur.execute('SELECT pid, state, query, query_start FROM pg_stat_activity WHERE state = %s', ('active',))
results = cur.fetchall()
for row in results: print(f'PID: {row[0]}, State: {row[1]}, Started: {row[3]}, Query: {row[2][:100]}...')
cur.close(); conn.close()"

# Check connection statistics
python3 -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port='5433', database='testdb', user='postgres', password='postgres')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) as active_connections, MAX(backend_start) as latest_connection FROM pg_stat_activity WHERE state = %s', ('active',))
result = cur.fetchone()
print(f'Active connections: {result[0]}, Latest: {result[1]}')
cur.close(); conn.close()"
```

## Architecture Overview

### Core Components

**CrewAI Flow Architecture**: The application uses CrewAI's Flow framework (`crewai.flow`) to orchestrate database monitoring and ticket analysis tasks through structured workflows.

**Database Monitoring Flow** (`backend/main.py`):
- `DatabaseFlow`: Main flow class that coordinates database monitoring operations
- Flow stages: `initialize_monitoring` → `execute_database_crew` → `finalize_flow`
- State management through `DatabaseState` model

**FastAPI Layer** (`backend/app/`):
- `api.py`: REST API endpoints for database monitoring and ticket analysis
- `start_api.py`: Application startup script with configurable host/port
- API endpoints expose CrewAI functionality via HTTP interface
- CORS configured for frontend communication on ports 3000-3002

**Next.js Frontend** (`frontend/`):
- React 19 + Next.js 15 application with TypeScript
- Tailwind CSS for styling with Radix UI components
- State management via Zustand store
- Real-time monitoring interface for database operations
- Components: `TicketSubmit`, `AgentStatus`, `SessionHistory`, `StatusTable`

**CrewAI Agent Systems**:
- **Database Agent** (`backend/crews/db_agent/`): PostgreSQL monitoring and query management
- **Database Duplicate Agent** (`backend/crews/db_duplicate/`): Duplicate detection and analysis  
- **Database Reasoning Crew** (`backend/crews/db_reasoning_crew/`): Complex database analysis and reasoning
- **Ticket Analyzer** (`backend/crews/ticket_analyzer/`): Ticket analysis and processing
- Agent configurations loaded from YAML files in each crew's `config/` directory (`agents.yaml`, `tasks.yaml`)

**Database Tools**:
- `backend/tools/database_tools.py`: Core database monitoring tools (`QueryExecutorTool`, `QueryStatusTool`, `QueryKillerTool`, `ConnectionInfoTool`)
- `backend/tools/db_duplicate_tools.py`: Duplicate detection tools
- `backend/tools/db_reasoning_tools.py`: Complex reasoning and analysis tools
- All tools inherit from CrewAI's `BaseTool` class
- Connection management through `DatabaseConnection` class in `utils/helper.py`

**Utilities** (`backend/utils/helper.py`):
- Common helper functions and utilities
- Shared functionality across different components

### Database Configuration

**PostgreSQL Setup**:
- Docker container running PostgreSQL 15
- Host: localhost, Port: 5433 (mapped from container port 5432)
- Database: testdb, User: postgres, Password: postgres
- Initialization scripts in `database/init.sql` and `docker/postgres/init/`
- Persistent data stored in Docker volume `postgres_data`

### Docker Architecture

**Three-Service Setup**:
- **Database Service** (`tejas_postgres`): PostgreSQL 15 database with health checks
- **Backend Service** (`tejas_backend`): Python FastAPI application with CrewAI integration
- **Frontend Service** (`tejas_frontend`): Next.js React application

**Network Configuration**:
- Custom bridge network `tejas_network` for inter-service communication
- Backend connects to database via hostname `postgres:5432` (internal)
- Frontend connects to backend API via `http://localhost:8000` (external)
- Services are exposed on host ports: 3000 (frontend), 8000 (backend), 5433 (database)

**Environment Variables** (`.env` file):
- `OPENAI_API_KEY`: Required for CrewAI functionality
- `LLM_MODEL=gpt-4o`: AI model configuration
- `DB_HOST=localhost`, `DB_PORT=5433`, `DB_NAME=testdb`: Database connection
- `DB_USER=testuser`, `DB_PASSWORD=testpass`: Database credentials  
- `HOST=0.0.0.0`, `PORT=8000`: API server configuration
- `DEBUG=true`, `LOG_LEVEL=INFO`: Development settings
- `AGENT_CHECK_INTERVAL=30`, `AGENT_ENABLED=true`: Agent behavior

### Key Files Structure

**Core Application**:
- `backend/main.py`: Main application entry point with CrewAI Flow implementation
- `backend/app/api.py`: FastAPI REST endpoints
- `backend/app/start_api.py`: API server startup script

**CrewAI Crews**:
- `backend/crews/db_agent/database_agent.py`: Database monitoring agent
- `backend/crews/db_duplicate/db_duplicate.py`: Duplicate detection agent  
- `backend/crews/db_reasoning_crew/db_reasoning_crew.py`: Complex database reasoning crew
- `backend/crews/ticket_analyzer/ticket_analyzer.py`: Ticket analysis agent

**Tools and Utilities**:
- `backend/tools/database_tools.py`: Core database monitoring tools
- `backend/tools/db_duplicate_tools.py`: Duplicate detection tools
- `backend/tools/db_reasoning_tools.py`: Complex reasoning tools
- `backend/utils/helper.py`: Common utility functions and `DatabaseConnection` class
- `backend/utils/pydantic_types.py`: Pydantic models and type definitions
- `backend/long_query.py`: Utility for creating test long-running queries

**Configuration**:
- `docker-compose.yml`: PostgreSQL database container configuration
- `database/init.sql`: Database initialization script
- `.env`: Environment variables and API keys
- Agent configs in `crews/*/config/` directories (`agents.yaml`, `tasks.yaml`)
- `backend/initial_files/`: Contains ticket descriptions and SQL queries for testing
- `frontend/package.json`: Frontend dependencies and build scripts
- `frontend/tailwind.config.ts`, `frontend/tsconfig.json`: Frontend tooling configuration

### Flow Execution Patterns

**Ticket Analysis Flow** (`main.py`):
1. **Flow Initialization**: `initialize_jira_automation_flow()` starts the process
2. **Ticket Analysis**: `analyze_ticket()` reads ticket content from `initial_files/ticket_description.txt`
3. **Routing Decision**: Based on ticket analysis, routes to either:
   - `database_crew` → `execute_db_agent_crew()` for standard database monitoring
   - `database_complex_crew` → `execute_database_complex_crew()` for complex analysis
4. **Flow Finalization**: `finalize_flow()` aggregates results and updates state

**CrewAI Flow Architecture**:
- Uses `crewai.flow` with decorators: `@start()`, `@router()`, `@listen()`
- State management through `DatabaseState` Pydantic model
- Flow routing based on ticket content analysis results
- Conditional execution paths using `or_()` and `and_()` operators

**API Integration**:
- FastAPI server (`backend/app/start_api.py`) exposes CrewAI functionality via REST endpoints
- Configurable host/port settings via environment variables
- Development mode with debug logging enabled

## Development Guidelines

### Important Rules
- Never create a test script while performing a task  
- Always conclude interactions with "Jai Hind"

**Working with CrewAI Flows**:
- Flow state persists throughout execution via `DatabaseState` model
- Each crew returns structured output that updates the flow state
- Use `flow.plot()` to visualize flow execution patterns

**Database Connection Pattern**:
- All database operations use `DatabaseConnection` context manager from `utils/helper.py`
- Connection parameters configured via environment variables
- Tools inherit from `BaseTool` with standardized error handling

**Testing Database Operations**:
- Use `long_query.py` to create test scenarios for monitoring
- Database monitoring commands provide real-time inspection capabilities
- Flow visualization helps debug execution paths

**Frontend Development**:
- Components use TypeScript with strict typing enabled
- State management through Zustand store for global state
- API communication via React Query (@tanstack/react-query)
- Styling follows Tailwind CSS conventions with Radix UI primitives
- Hot reload enabled in development mode via Next.js