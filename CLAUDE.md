# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r backend/app/requirements.txt

# Set up environment variables (copy from .env.example if available)
# Required: OPENAI_API_KEY, DB_* settings
```

### Database Setup
```bash
# Start PostgreSQL database
docker-compose up -d

# Check database connection
python3 -c "import psycopg2; print('Connection successful')" 2>/dev/null && echo "✅ Connected" || echo "❌ Connection failed"
```

### Application Execution
```bash
# Run the main database monitoring flow (CrewAI Flow)
cd backend && python main.py

# Start the FastAPI server
cd backend && python app/start_api.py

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