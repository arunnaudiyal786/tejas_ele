"""
Integration module to connect the CrewAI agent with the FastAPI application.
"""

import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from flow import terminate_query_sync, process_all_open_tickets

# Create router for agent endpoints
router = APIRouter(prefix="/api/agent", tags=["agent"])

class TerminationRequest(BaseModel):
    identifier: int
    identifier_type: str = "ticket"  # ticket, process, or query

@router.post("/terminate-query")
async def terminate_query_endpoint(request: TerminationRequest) -> Dict[str, Any]:
    """
    Endpoint to trigger query termination through the agent.
    
    Args:
        request: TerminationRequest containing identifier and type
        
    Returns:
        Agent execution result
    """
    try:
        if request.identifier_type not in ['ticket', 'process', 'query']:
            raise HTTPException(
                status_code=400,
                detail="identifier_type must be 'ticket', 'process', or 'query'"
            )
        
        result = terminate_query_sync(request.identifier, request.identifier_type)
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=f"Agent failed to process request: {result.get('error', 'Unknown error')}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute termination request: {str(e)}"
        )

@router.post("/process-open-tickets")
async def process_open_tickets_endpoint() -> Dict[str, Any]:
    """
    Endpoint to process all open tickets for potential query termination.
    
    Returns:
        Processing results for all open tickets
    """
    try:
        result = process_all_open_tickets()
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process open tickets: {str(e)}"
        )

@router.get("/health")
async def agent_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the agent system.
    
    Returns:
        Agent system health status
    """
    try:
        # Simple health check - try to import the agent modules
        from agents.agents import QueryTerminationAgent
        from agents.query_management_tool import get_query_status
        
        return {
            "status": "healthy",
            "message": "Agent system is operational",
            "components": {
                "agent": "healthy",
                "tools": "healthy",
                "flow": "healthy"
            }
        }
        
    except ImportError as e:
        return {
            "status": "unhealthy",
            "message": f"Missing dependencies: {str(e)}",
            "components": {
                "agent": "error",
                "tools": "error", 
                "flow": "error"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"System error: {str(e)}",
            "components": {
                "agent": "unknown",
                "tools": "unknown",
                "flow": "unknown"
            }
        }