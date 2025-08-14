# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Database Setup
```bash
# Start PostgreSQL database
docker-compose up -d

# Check database connection
python3 -c "import psycopg2; print('Connection successful')" 2>/dev/null && echo "✅ Connected" || echo "❌ Connection failed"
```

### Application Execution
```bash
# Run the main database monitoring flow
cd backend && python main.py

# Start the FastAPI server
cd backend && python app/start_api.py

# Run database monitoring crew directly
cd backend && python -c "from crews.db_agent.database_agent import execute_database_monitoring; result = execute_database_monitoring(); print('Result:', result['result'])"

# Execute a long-running test query
cd backend && python long_query.py

# Run ticket analyzer crew
cd backend && python -c "from crews.ticket_analyzer.ticket_analyzer import execute_ticket_analysis; result = execute_ticket_analysis(); print('Result:', result)"
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

**CrewAI Agent Systems**:
- **Database Agent** (`backend/crews/db_agent/`): PostgreSQL monitoring and query management
- **Database Duplicate Agent** (`backend/crews/db_duplicate/`): Duplicate detection and analysis
- **Ticket Analyzer** (`backend/crews/ticket_analyzer/`): Ticket analysis and processing
- Agent configurations loaded from YAML files (`config/agents.yaml`, `config/tasks.yaml`)

**Database Tools** (`backend/tools/database_tools.py`):
- Custom CrewAI tools that inherit from `BaseTool`
- Tools: `QueryStatusTool`, `QueryKillerTool`, `ConnectionInfoTool`
- Connection management through `DatabaseConnection` class

**Utilities** (`backend/utils/helper.py`):
- Common helper functions and utilities
- Shared functionality across different components

### Database Configuration

**PostgreSQL Setup**:
- Docker container running PostgreSQL 15
- Host: localhost, Port: 5433 (mapped from container port 5432)
- Database: testdb, User: postgres, Password: postgres
- Initialization scripts in `database/init.sql` and `docker/postgres/init/`

**Environment Variables**:
- `DB_HOST=localhost`
- `DB_PORT=5433`
- `DB_NAME=testdb`
- `DB_USER=postgres`
- `DB_PASSWORD=postgres`
- `HOST=0.0.0.0` (API server host)
- `PORT=8000` (API server port)
- `DEBUG=true` (development mode)
- `LOG_LEVEL=info`

### Key Files Structure

**Core Application**:
- `backend/main.py`: Main application entry point with CrewAI Flow implementation
- `backend/app/api.py`: FastAPI REST endpoints
- `backend/app/start_api.py`: API server startup script

**CrewAI Agents**:
- `backend/crews/db_agent/database_agent.py`: Database monitoring agent
- `backend/crews/db_duplicate/database_agent.py`: Duplicate detection agent
- `backend/crews/ticket_analyzer/ticket_analyzer.py`: Ticket analysis agent

**Tools and Utilities**:
- `backend/tools/database_tools.py`: Custom database monitoring tools
- `backend/utils/helper.py`: Common utility functions
- `backend/long_query.py`: Utility for creating test long-running queries

**Configuration**:
- `docker-compose.yml`: PostgreSQL database container configuration
- `database/init.sql`: Database initialization script
- Agent configs in `crews/*/config/` directories

### Flow Execution Patterns

**Database Monitoring Flow**:
1. **Flow Initialization**: Sets up database monitoring context
2. **Crew Execution**: Runs database administrator agent with monitoring tasks
3. **Task Execution**: Agent uses tools to check query status, connection info, and manage queries
4. **Flow Finalization**: Aggregates results and updates flow state

**API Integration**:
- REST endpoints provide HTTP access to CrewAI functionality
- Configurable server settings via environment variables
- Support for both development and production deployment

The system is designed as a comprehensive database monitoring and ticket analysis platform, providing both automated CrewAI-based processing and manual database inspection capabilities through multiple interfaces (Flow, API, CLI).