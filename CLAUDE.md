# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Long-Running Query Management System** that demonstrates real database session monitoring and AI-powered ticket resolution. The system allows users to:

1. Submit long-running SQL queries against a PostgreSQL database with 1M+ records
2. Create support tickets for problematic queries
3. Have a CrewAI agent automatically terminate database sessions and resolve tickets

## Architecture

- **Frontend**: Vanilla HTML/CSS/JavaScript (no frameworks)
- **Backend**: FastAPI (Python) with async query execution
- **Main Database**: PostgreSQL (sample data with 1M orders, 100K customers, 10K products)
- **Metadata Storage**: SQLite (queries, tickets, session tracking)
- **AI Agent**: CrewAI with specialized tools for database session management

## Key Components

### Backend Services (`/app`)
- `main.py` - FastAPI web server with REST APIs
- `database.py` - Database operations (PostgreSQL + SQLite)
- `agent.py` - CrewAI agent for automatic session termination
- `setup_db.py` - PostgreSQL database initialization script
- `run_with_agent.py` - Startup script running both web server and AI agent

### Frontend (`/static`)
- `index.html` - Main query execution interface
- `ticket.html` - Ticket management interface
- `style.css` - Styling for both pages
- `script.js` - JavaScript for main page functionality
- `ticket.js` - JavaScript for ticket management

## Common Development Tasks

### Database Setup
```bash
# Install PostgreSQL locally first, then:
createdb longquery_demo
python app/setup_db.py
```

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Full system (web server + AI agent)
python app/run_with_agent.py

# Web server only (for development)
python app/main.py

# Agent only (for testing)
python app/agent.py
```

### Testing Setup
```bash
# Verify all components work correctly
python test_setup.py
```

### Development Server
```bash
# FastAPI with auto-reload (disable agent during development)
cd app && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Database Schema

### PostgreSQL (Main Data)
- `customers` - 100K customer records
- `products` - 10K product records  
- `orders` - 1M order records (intentionally no indexes for slow queries)

### SQLite (App Metadata)
- `queries` - Query execution tracking with PostgreSQL session PIDs
- `tickets` - Support tickets linked to queries
- `active_sessions` - PostgreSQL session monitoring

## API Endpoints

### Query Management
- `POST /api/query` - Execute SQL query
- `GET /api/queries` - List all queries with status
- `GET /api/queries/{id}` - Get specific query status
- `GET /api/sample-queries` - Get predefined slow queries

### Ticket Management
- `POST /api/tickets` - Create support ticket
- `GET /api/tickets` - List all tickets
- `GET /api/tickets/open` - Get open tickets (for agent)
- `POST /api/tickets/{id}/resolve` - Resolve ticket

### Session Management
- `GET /api/sessions` - List active PostgreSQL sessions
- `POST /api/sessions/terminate` - Terminate session by PID

## CrewAI Agent

The AI agent automatically:
1. Monitors open tickets every 30 seconds
2. Identifies tickets with running PostgreSQL queries
3. Terminates problematic database sessions
4. Resolves tickets with detailed explanations

**Tools Available:**
- `postgresql_session_tool` - Query/terminate PostgreSQL sessions
- `ticket_management_tool` - List/resolve support tickets

## Configuration

Copy `.env.example` to `.env` and configure:
- PostgreSQL connection details
- OpenAI API key (required for CrewAI)
- Agent monitoring interval

## Predefined Slow Queries

The system includes 4 sample queries designed to run 2-15 minutes:
1. Complex aggregation by country (heavy joins)
2. Cartesian product analysis (cross joins)
3. Recursive Fibonacci calculation (CPU intensive)
4. Multi-table join with string operations

## Development Notes

- PostgreSQL intentionally has no indexes on join columns to ensure slow queries
- Real database sessions are tracked via `pg_stat_activity` and `pg_backend_pid()`
- Session termination uses `pg_terminate_backend()` for actual session killing
- SQLite is used for lightweight app metadata to avoid affecting main database performance
- Frontend updates in real-time via JavaScript polling (no WebSockets needed)

## Troubleshooting

### PostgreSQL Connection Issues
- Verify PostgreSQL is running: `pg_ctl status`
- Check database exists: `psql -l | grep longquery_demo`
- Verify credentials in database.py match your PostgreSQL setup

### Agent Not Processing Tickets
- Ensure OpenAI API key is set in environment
- Check agent logs for CrewAI errors
- Verify tickets have valid PostgreSQL session PIDs

### Slow Queries Not Appearing
- Run `python test_setup.py` to verify database population
- Check that tables have expected record counts (1M orders, 100K customers)
- Ensure no accidental indexes were created on join columns

## File Structure
```
/app/                 # Backend Python code
  main.py             # FastAPI server
  database.py         # Database operations
  agent.py            # CrewAI agent
  setup_db.py         # Database initialization
  run_with_agent.py   # Full system startup
/static/              # Frontend files
  *.html              # Web pages
  *.css               # Styling
  *.js                # Client-side logic
requirements.txt      # Python dependencies
test_setup.py         # System verification
.env.example          # Configuration template
```