"""
Simple and concise database tools with args_schema validation.
"""

import os
import psycopg2
import time
from typing import Dict, Any, Optional
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# ========== INPUT SCHEMAS ==========

class DatabaseConnectionInput(BaseModel):
    """Input schema for database connection."""
    query: str = Field(default="test", description="SQL query to execute or 'test' for connection check")

class DeleteDuplicatesInput(BaseModel):
    """Input schema for delete duplicates operation."""
    table_name: str = Field(description="Table name to remove duplicates from")
    columns: str = Field(default="", description="Comma-separated columns for duplicate detection")
    dry_run: bool = Field(default=True, description="Only count duplicates without deleting")

class InsertRowInput(BaseModel):
    """Input schema for insert row operation."""
    table_name: str = Field(description="Table name to insert into")
    row_data: Dict[str, Any] = Field(description="Row data as dictionary")
    validate_only: bool = Field(default=False, description="Only validate without inserting")

class KillSessionInput(BaseModel):
    """Input schema for session management."""
    action: str = Field(description="Action: 'list' or 'kill'")
    session_pid: Optional[str] = Field(default=None, description="Session PID to kill")
    reason: str = Field(default="", description="Reason for termination")

class JiraTicketInput(BaseModel):
    """Input schema for Jira ticket analysis."""
    ticket_data: Dict[str, Any] = Field(description="Jira ticket data dictionary")


# ========== TOOLS ==========

class DatabaseConnectionTool(BaseTool):
    """Test database connection and run simple queries."""
    
    name: str = "Database Connection"
    description: str = "Test database connection and execute safe queries"
    args_schema: type = DatabaseConnectionInput

    def _run(self, query: str = "test") -> str:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5433'),
                database=os.getenv('DB_NAME', 'testdb'),
                user=os.getenv('DB_USER', 'testuser'),
                password=os.getenv('DB_PASSWORD', 'testpass')
            )
            cursor = conn.cursor()
            
            if query == "test":
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                table_count = cursor.fetchone()[0]
                result = f"✅ Connected successfully. Found {table_count} tables."
            else:
                if query.lower().startswith(('select', 'show', 'describe')):
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    result = f"✅ Query executed. Returned {len(rows)} rows."
                else:
                    result = "❌ Only SELECT queries allowed for safety"
            
            cursor.close()
            conn.close()
            return result
            
        except Exception as e:
            return f"❌ Connection failed: {str(e)}"


class DeleteDuplicateRowsTool(BaseTool):
    """Remove duplicate rows from database tables."""
    
    name: str = "Delete Duplicates"
    description: str = "Find and remove duplicate rows from database tables"
    args_schema: type = DeleteDuplicatesInput

    def _run(self, table_name: str, columns: str = "", dry_run: bool = True) -> str:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5433'),
                database=os.getenv('DB_NAME', 'testdb'),
                user=os.getenv('DB_USER', 'testuser'),
                password=os.getenv('DB_PASSWORD', 'testpass')
            )
            cursor = conn.cursor()
            
            # Check table exists
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", (table_name,))
            if not cursor.fetchone()[0]:
                return f"❌ Table '{table_name}' not found"
            
            # Auto-detect columns if not provided
            if not columns:
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = %s AND column_name NOT IN ('id', 'created_at', 'updated_at')
                    ORDER BY ordinal_position LIMIT 3
                """, (table_name,))
                cols = [row[0] for row in cursor.fetchall()]
                columns = ", ".join(cols)
            
            # Find duplicates
            cursor.execute(f"""
                SELECT {columns}, COUNT(*) as count
                FROM {table_name}
                GROUP BY {columns}
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
            if not duplicates:
                result = f"✅ No duplicates found in {table_name}"
            elif dry_run:
                total_dupes = sum(row[-1] - 1 for row in duplicates)
                result = f"🔍 Found {len(duplicates)} duplicate groups ({total_dupes} rows to delete)"
            else:
                # Delete duplicates keeping oldest by ID
                cursor.execute(f"""
                    DELETE FROM {table_name} WHERE id IN (
                        SELECT id FROM (
                            SELECT id, ROW_NUMBER() OVER (PARTITION BY {columns} ORDER BY id) as rn
                            FROM {table_name}
                        ) t WHERE rn > 1
                    )
                """)
                deleted = cursor.rowcount
                conn.commit()
                result = f"✅ Deleted {deleted} duplicate rows from {table_name}"
            
            cursor.close()
            conn.close()
            return result
            
        except Exception as e:
            return f"❌ Error: {str(e)}"


class InsertRowTool(BaseTool):
    """Insert new rows into database tables."""
    
    name: str = "Insert Row"
    description: str = "Insert new rows into database tables with validation"
    args_schema: type = InsertRowInput

    def _run(self, table_name: str, row_data: Dict[str, Any], validate_only: bool = False) -> str:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5433'),
                database=os.getenv('DB_NAME', 'testdb'),
                user=os.getenv('DB_USER', 'testuser'),
                password=os.getenv('DB_PASSWORD', 'testpass')
            )
            cursor = conn.cursor()
            
            # Check table exists
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", (table_name,))
            if not cursor.fetchone()[0]:
                return f"❌ Table '{table_name}' not found"
            
            # Get required columns
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = %s AND is_nullable = 'NO' AND column_default IS NULL
            """, (table_name,))
            required_cols = [row[0] for row in cursor.fetchall()]
            
            # Validate required columns
            missing = [col for col in required_cols if col not in row_data and col != 'id']
            if missing:
                return f"❌ Missing required columns: {missing}"
            
            if validate_only:
                return f"✅ Validation passed for {table_name}"
            
            # Insert row
            columns = list(row_data.keys())
            values = list(row_data.values())
            placeholders = ', '.join(['%s'] * len(values))
            
            cursor.execute(f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({placeholders})
                RETURNING id
            """, values)
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return f"✅ Inserted row in {table_name} with ID: {new_id}"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"


class KillSessionTool(BaseTool):
    """Manage database sessions."""
    
    name: str = "Kill Session"
    description: str = "List or terminate database sessions"
    args_schema: type = KillSessionInput

    def _run(self, action: str, session_pid: Optional[str] = None, reason: str = "") -> str:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5433'),
                database=os.getenv('DB_NAME', 'testdb'),
                user=os.getenv('DB_USER', 'testuser'),
                password=os.getenv('DB_PASSWORD', 'testpass')
            )
            cursor = conn.cursor()
            
            if action == "list":
                cursor.execute("""
                    SELECT pid, usename, application_name, state, 
                           EXTRACT(EPOCH FROM (NOW() - query_start))::int as seconds
                    FROM pg_stat_activity 
                    WHERE pid != pg_backend_pid() AND state IS NOT NULL
                    ORDER BY query_start DESC
                """)
                sessions = cursor.fetchall()
                
                if not sessions:
                    result = "✅ No other sessions found"
                else:
                    result = f"📋 Found {len(sessions)} sessions:\n"
                    for pid, user, app, state, seconds in sessions[:10]:
                        age = f"{seconds//60}m" if seconds else "0s"
                        result += f"  PID {pid}: {user} ({state}) - {age}\n"
            
            elif action == "kill":
                if not session_pid:
                    return "❌ session_pid required for kill action"
                
                cursor.execute("SELECT pg_terminate_backend(%s)", (session_pid,))
                success = cursor.fetchone()[0]
                
                if success:
                    result = f"✅ Terminated session {session_pid}"
                    if reason:
                        result += f" - Reason: {reason}"
                else:
                    result = f"❌ Failed to terminate session {session_pid}"
            
            else:
                result = "❌ Action must be 'list' or 'kill'"
            
            cursor.close()
            conn.close()
            return result
            
        except Exception as e:
            return f"❌ Error: {str(e)}"


class JiraTicketTool(BaseTool):
    """Analyze Jira tickets for database operations."""
    
    name: str = "Jira Ticket Analyzer"
    description: str = "Extract database operation requirements from Jira tickets"
    args_schema: type = JiraTicketInput

    def _run(self, ticket_data: Dict[str, Any]) -> str:
        try:
            ticket_id = ticket_data.get('ticket_id', 'Unknown')
            summary = ticket_data.get('summary', '')
            description = ticket_data.get('description', '')
            priority = ticket_data.get('priority', 'Medium')
            
            text = f"{summary} {description}".lower()
            
            # Detect operation type
            if any(word in text for word in ['duplicate', 'remove duplicate']):
                operation = "delete_duplicates"
            elif any(word in text for word in ['insert', 'add', 'create']):
                operation = "insert_row"
            elif any(word in text for word in ['kill', 'terminate', 'session']):
                operation = "kill_session"
            else:
                operation = "unknown"
            
            # Detect table
            tables = ['member_enrollment', 'product_catalog', 'provider_network', 'claims_authorization']
            table = next((t for t in tables if t in text or t.replace('_', ' ') in text), 'unknown')
            
            # Assess complexity
            complexity = "High" if any(word in text for word in ['urgent', 'critical']) else "Medium"
            
            return f"""
📋 Ticket Analysis: {ticket_id}
🎯 Operation: {operation}
📊 Table: {table}
⚡ Priority: {priority}
🔧 Complexity: {complexity}

Summary: {summary[:100]}...
"""
            
        except Exception as e:
            return f"❌ Analysis error: {str(e)}"


# Export all tools
__all__ = [
    'DatabaseConnectionTool',
    'DeleteDuplicateRowsTool', 
    'InsertRowTool',
    'KillSessionTool',
    'JiraTicketTool'
]