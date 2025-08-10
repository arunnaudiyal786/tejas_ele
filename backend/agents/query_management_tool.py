"""
Custom tool for managing long-running PostgreSQL queries.
Provides functions to check status, terminate queries, and update tickets.
"""

import sqlite3
import psycopg2
from typing import Dict, Any, Optional
from crewai_tools import tool
import os
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'longquery_demo'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': os.getenv('DB_PORT', '5432')
}

@tool
def get_query_status(process_id: int) -> Dict[str, Any]:
    """
    Get the status of a PostgreSQL query by process ID.
    
    Args:
        process_id: The PostgreSQL process ID (PID) of the query
        
    Returns:
        Dict containing query status information
    """
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Query pg_stat_activity to get process information
        query = """
        SELECT 
            pid,
            usename,
            application_name,
            client_addr,
            state,
            query,
            query_start,
            state_change,
            backend_start,
            EXTRACT(EPOCH FROM (NOW() - query_start)) as duration_seconds
        FROM pg_stat_activity 
        WHERE pid = %s;
        """
        
        cursor.execute(query, (process_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                "success": True,
                "process_id": result[0],
                "username": result[1],
                "application_name": result[2],
                "client_address": result[3],
                "state": result[4],
                "query": result[5],
                "query_start": str(result[6]),
                "state_change": str(result[7]),
                "backend_start": str(result[8]),
                "duration_seconds": float(result[9]) if result[9] else 0,
                "is_active": result[4] == 'active'
            }
        else:
            return {
                "success": False,
                "message": f"No active process found with PID {process_id}",
                "process_id": process_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "process_id": process_id
        }
    finally:
        if 'conn' in locals():
            conn.close()

@tool
def kill_query(process_id: int) -> Dict[str, Any]:
    """
    Terminate a PostgreSQL query by process ID using pg_terminate_backend.
    
    Args:
        process_id: The PostgreSQL process ID (PID) to terminate
        
    Returns:
        Dict containing termination result
    """
    try:
        # First check if the process exists
        status = get_query_status(process_id)
        if not status.get("success"):
            return {
                "success": False,
                "message": f"Process {process_id} not found or already terminated",
                "process_id": process_id
            }
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Use pg_terminate_backend to kill the process
        cursor.execute("SELECT pg_terminate_backend(%s);", (process_id,))
        result = cursor.fetchone()[0]
        
        conn.commit()
        
        if result:
            return {
                "success": True,
                "message": f"Successfully terminated process {process_id}",
                "process_id": process_id,
                "terminated_at": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": f"Failed to terminate process {process_id}. Process may have already ended.",
                "process_id": process_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "process_id": process_id
        }
    finally:
        if 'conn' in locals():
            conn.close()

@tool
def update_ticket_status(ticket_id: int, status: str, resolution_notes: str = "") -> Dict[str, Any]:
    """
    Update ticket status in the SQLite database with resolution information.
    
    Args:
        ticket_id: The ticket ID to update
        status: New status ('resolved', 'in_progress', 'closed', etc.)
        resolution_notes: Notes about the resolution
        
    Returns:
        Dict containing update result
    """
    try:
        # Connect to SQLite metadata database
        conn = sqlite3.connect("/Users/arunnaudiyal/Arun/Deloitte/Tejas/Code/tejas_ele/app_metadata.db")
        cursor = conn.cursor()
        
        # Check if ticket exists
        cursor.execute("SELECT id, status FROM tickets WHERE id = ?", (ticket_id,))
        ticket = cursor.fetchone()
        
        if not ticket:
            return {
                "success": False,
                "message": f"Ticket {ticket_id} not found",
                "ticket_id": ticket_id
            }
        
        # Add resolution_notes and resolved_at columns if they don't exist
        try:
            cursor.execute("ALTER TABLE tickets ADD COLUMN resolution_notes TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute("ALTER TABLE tickets ADD COLUMN resolved_at DATETIME")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Update ticket status
        update_time = datetime.now().isoformat() if status in ['resolved', 'closed'] else None
        cursor.execute(
            """
            UPDATE tickets 
            SET status = ?, resolution_notes = ?, resolved_at = ?
            WHERE id = ?
            """,
            (status, resolution_notes, update_time, ticket_id)
        )
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"Ticket {ticket_id} updated to status: {status}",
            "ticket_id": ticket_id,
            "new_status": status,
            "resolution_notes": resolution_notes,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticket_id": ticket_id
        }
    finally:
        if 'conn' in locals():
            conn.close()

@tool
def get_ticket_details(ticket_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a ticket including associated query information.
    
    Args:
        ticket_id: The ticket ID to retrieve
        
    Returns:
        Dict containing ticket details
    """
    try:
        # Connect to SQLite metadata database
        conn = sqlite3.connect("/Users/arunnaudiyal/Arun/Deloitte/Tejas/Code/tejas_ele/app_metadata.db")
        cursor = conn.cursor()
        
        # Get ticket information
        cursor.execute("""
            SELECT id, query_id, description, priority, created_at, status, 
                   resolution_notes, resolved_at
            FROM tickets WHERE id = ?
        """, (ticket_id,))
        
        ticket = cursor.fetchone()
        
        if not ticket:
            return {
                "success": False,
                "message": f"Ticket {ticket_id} not found"
            }
        
        # Get associated query information if query_id exists
        query_info = None
        if ticket[1]:  # query_id
            cursor.execute("""
                SELECT id, query_text, status, created_at, process_id
                FROM queries WHERE id = ?
            """, (ticket[1],))
            query_result = cursor.fetchone()
            
            if query_result:
                query_info = {
                    "query_id": query_result[0],
                    "query_text": query_result[1],
                    "status": query_result[2],
                    "created_at": query_result[3],
                    "process_id": query_result[4]
                }
        
        return {
            "success": True,
            "ticket": {
                "id": ticket[0],
                "query_id": ticket[1],
                "description": ticket[2],
                "priority": ticket[3],
                "created_at": ticket[4],
                "status": ticket[5],
                "resolution_notes": ticket[6],
                "resolved_at": ticket[7]
            },
            "query_info": query_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticket_id": ticket_id
        }
    finally:
        if 'conn' in locals():
            conn.close()