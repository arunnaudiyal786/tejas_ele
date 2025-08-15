from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import os
import json
import glob
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import kickoff_database_flow_with_ticket

app = FastAPI(
    title="Database Monitoring API",
    description="FastAPI wrapper for CrewAI Database Monitoring Flow"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active sessions
active_sessions = {}

class TicketRequest(BaseModel):
    ticket_content: str

class SessionStatus(BaseModel):
    session_id: str
    status: str
    stage: str
    result: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None

def run_flow_background(session_id: str, ticket_content: str):
    """Run flow in background and update session status"""
    try:
        active_sessions[session_id] = {
            "status": "running",
            "stage": "initializing",
            "started_at": datetime.now().isoformat()
        }
        
        result = kickoff_database_flow_with_ticket(ticket_content)
        
        active_sessions[session_id].update({
            "status": "completed",
            "stage": "finalized",
            "result": result,
            "completed_at": datetime.now().isoformat()
        })
    except Exception as e:
        active_sessions[session_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })

@app.post("/start-monitoring")
async def start_monitoring(request: TicketRequest, background_tasks: BackgroundTasks):
    """Start the database monitoring flow with ticket content"""
    from main import generate_session_id
    
    session_id = generate_session_id()
    
    # Start flow in background
    background_tasks.add_task(run_flow_background, session_id, request.ticket_content)
    
    return {
        "session_id": session_id,
        "status": "started",
        "message": "Flow started successfully"
    }

@app.get("/status/{session_id}")
async def get_status(session_id: str):
    """Get status of a specific session"""
    if session_id in active_sessions:
        session = active_sessions[session_id]
        return SessionStatus(
            session_id=session_id,
            status=session.get("status"),
            stage=session.get("stage", "unknown"),
            result=session.get("result"),
            error=session.get("error"),
            started_at=session.get("started_at"),
            completed_at=session.get("completed_at")
        )
    
    # Check if session exists in results folder
    result_path = f"results/{session_id}/query_resolution.json"
    if os.path.exists(result_path):
        with open(result_path, 'r') as f:
            result = json.load(f)
        return SessionStatus(
            session_id=session_id,
            status="completed",
            stage="finalized",
            result={"data": result},
            started_at="unknown",
            completed_at="unknown"
        )
    
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions")
async def get_sessions():
    """Get list of all sessions"""
    sessions = []
    
    # Get active sessions
    for sid, data in active_sessions.items():
        sessions.append({
            "session_id": sid,
            "status": data.get("status"),
            "started_at": data.get("started_at"),
            "completed_at": data.get("completed_at")
        })
    
    # Get historical sessions from results folder
    result_dirs = glob.glob("results/*/")
    for dir_path in result_dirs:
        session_id = os.path.basename(os.path.normpath(dir_path))
        if session_id not in active_sessions:
            result_file = os.path.join(dir_path, "query_resolution.json")
            if os.path.exists(result_file):
                # Parse session_id for timestamp
                try:
                    date_part = session_id.split('_')[0]
                    time_part = session_id.split('_')[1]
                    year = date_part[:4]
                    month = date_part[4:6]
                    day = date_part[6:8]
                    hour = time_part[:2]
                    minute = time_part[2:4]
                    started_at = f"{year}-{month}-{day}T{hour}:{minute}:00"
                except:
                    started_at = "unknown"
                
                sessions.append({
                    "session_id": session_id,
                    "status": "completed",
                    "started_at": started_at,
                    "completed_at": started_at
                })
    
    # Sort by started_at (newest first)
    sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    
    return {"sessions": sessions}

@app.get("/session/{session_id}/result")
async def get_session_result(session_id: str):
    """Get detailed result of a specific session"""
    result_path = f"results/{session_id}/query_resolution.json"
    
    if os.path.exists(result_path):
        with open(result_path, 'r') as f:
            result = json.load(f)
        return {
            "session_id": session_id,
            "result": result
        }
    
    if session_id in active_sessions and active_sessions[session_id].get("result"):
        return {
            "session_id": session_id,
            "result": active_sessions[session_id]["result"]
        }
    
    raise HTTPException(status_code=404, detail="Result not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)