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

# Run database monitoring crew directly
cd backend && python -c "from crews.db_agent.database_agent import execute_database_monitoring; result = execute_database_monitoring(); print('Result:', result['result'])"

# Execute a long-running test query
cd backend && python long_query.py
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

**CrewAI Flow Architecture**: The application uses CrewAI's Flow framework (`crewai.flow`) to orchestrate database monitoring tasks through a structured workflow.

**Database Monitoring Flow** (`backend/main.py`):
- `DatabaseFlow`: Main flow class that coordinates database monitoring operations
- Flow stages: `initialize_monitoring` → `execute_database_crew` → `finalize_flow`
- State management through `DatabaseState` model

**CrewAI Agent System** (`backend/crews/db_agent/`):
- Database Administrator agent with specialized tools for PostgreSQL monitoring
- Agent configuration loaded from YAML files (`config/agents.yaml`, `config/tasks.yaml`)
- Tools: `QueryStatusTool`, `QueryKillerTool`, `ConnectionInfoTool`

**Database Tools** (`backend/tools/database_tools.py`):
- Custom CrewAI tools that inherit from `BaseTool`
- Connection management through `DatabaseConnection` class
- Configuration loaded from `backend/config.yaml`

### Database Configuration

**PostgreSQL Setup**:
- Docker container running PostgreSQL 15
- Host: localhost, Port: 5433 (mapped from container port 5432)
- Database: testdb, User: postgres, Password: postgres
- Connection parameters stored in `backend/config.yaml`

**Environment Variables** (from backend README):
- `DB_HOST=localhost`
- `DB_PORT=5433`
- `DB_NAME=testdb`
- `DB_USER=postgres` (actual config uses 'postgres', not 'testuser')
- `DB_PASSWORD=postgres` (actual config uses 'postgres', not 'testpass')

### Key Files Structure

- `backend/main.py`: Main application entry point with CrewAI Flow implementation
- `backend/crews/db_agent/database_agent.py`: CrewAI agent and crew definitions
- `backend/tools/database_tools.py`: Custom database monitoring tools
- `backend/config.yaml`: Application and database configuration
- `backend/long_query.py`: Utility for creating test long-running queries
- `docker-compose.yml`: PostgreSQL database container configuration

### Flow Execution Pattern

1. **Flow Initialization**: Sets up database monitoring context
2. **Crew Execution**: Runs database administrator agent with monitoring tasks
3. **Task Execution**: Agent uses tools to check query status, connection info, and manage queries
4. **Flow Finalization**: Aggregates results and updates flow state

The system is designed for monitoring PostgreSQL database activity, particularly long-running queries, and provides both automated CrewAI-based monitoring and manual database inspection capabilities.