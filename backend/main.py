"""
Simple FastAPI backend for Long-Running Query Manager.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio
import sqlite3

from database import get_db_manager
from setup_db import get_sample_slow_queries

# Import agent integration
try:
    from agent_integration import router as agent_router
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="Long-Running Query Manager",
    version="1.0.0",
    description="Database session management system"
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static')
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Pydantic models
class QueryRequest(BaseModel):
    query_text: str
    query_name: Optional[str] = None

class TicketRequest(BaseModel):
    query_id: int
    description: str
    priority: Optional[str] = "medium"

# Serve HTML pages
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main page"""
    pages_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'pages')
    index_file = os.path.join(pages_dir, 'index.html')
    if os.path.exists(index_file):
        with open(index_file, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Welcome to Long-Running Query Manager</h1>")

@app.get("/tickets", response_class=HTMLResponse)
async def tickets_page():
    """Serve the tickets page"""
    pages_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'pages')
    ticket_file = os.path.join(pages_dir, 'ticket.html')
    if os.path.exists(ticket_file):
        with open(ticket_file, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Tickets Page</h1>")

# API endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/queries")
async def get_queries():
    """Get list of available sample queries"""
    return {"queries": get_sample_slow_queries()}

@app.post("/api/execute-query")
async def execute_query(request: QueryRequest):
    """Execute a SQL query"""
    try:
        db_manager = get_db_manager()
        # This is a simplified version - in production you'd want proper async handling
        result = await asyncio.create_task(
            asyncio.to_thread(db_manager.execute_query_sync, request.query_text)
        )
        return {"success": True, "query_id": result.get("query_id"), "message": "Query started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/active-queries")
async def get_active_queries():
    """Get list of active queries"""
    try:
        db_manager = get_db_manager()
        queries = db_manager.get_active_queries()
        return {"queries": queries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tickets")
async def create_ticket(request: TicketRequest):
    """Create a support ticket"""
    try:
        # Simple SQLite storage for tickets
        conn = sqlite3.connect("app_metadata.db")
        cursor = conn.cursor()
        
        # Create tickets table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER,
                description TEXT,
                priority TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'open'
            )
        """)
        
        cursor.execute(
            "INSERT INTO tickets (query_id, description, priority) VALUES (?, ?, ?)",
            (request.query_id, request.description, request.priority)
        )
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"success": True, "ticket_id": ticket_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tickets")
async def get_tickets():
    """Get all tickets"""
    try:
        conn = sqlite3.connect("app_metadata.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
        tickets = [
            {
                "id": row[0],
                "query_id": row[1], 
                "description": row[2],
                "priority": row[3],
                "created_at": row[4],
                "status": row[5]
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return {"tickets": tickets}
    except Exception as e:
        return {"tickets": []}

# Include agent router if available
if AGENT_AVAILABLE:
    app.include_router(agent_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)