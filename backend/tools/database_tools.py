from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import psycopg2
import os
from typing import Optional

class DatabaseConnection:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5433'),
            'database': os.getenv('DB_NAME', 'testdb'),
            'user': os.getenv('DB_USER', 'testuser'),
            'password': os.getenv('DB_PASSWORD', 'testpass')
        }
    
    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

class QueryStatusTool(BaseTool):
    name: str = "query_status_checker"
    description: str = "Check the status of a running database query using process ID or query text"
    
    def _run(self, query_text: Optional[str] = None, pid: Optional[int] = None) -> str:
        try:
            db = DatabaseConnection()
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    if pid:
                        cur.execute("""
                            SELECT pid, state, query, query_start 
                            FROM pg_stat_activity 
                            WHERE pid = %s
                        """, (pid,))
                    elif query_text:
                        cur.execute("""
                            SELECT pid, state, query, query_start 
                            FROM pg_stat_activity 
                            WHERE query ILIKE %s AND state = 'active'
                        """, (f"%{query_text}%",))
                    else:
                        # If no parameters provided, show all active queries
                        cur.execute("""
                            SELECT pid, state, query, query_start 
                            FROM pg_stat_activity 
                            WHERE state = 'active'
                        """)
                    
                    result = cur.fetchone()
                    if result:
                        return f"Query Status - PID: {result[0]}, State: {result[1]}, Started: {result[3]}"
                    return "No active query found"
        except Exception as e:
            return f"Error checking query status: {str(e)}"

class QueryKillerTool(BaseTool):
    name: str = "query_killer"
    description: str = "Kill a running database query using its process ID"
    
    def _run(self, pid: int) -> str:
        try:
            db = DatabaseConnection()
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_terminate_backend(%s)", (pid,))
                    result = cur.fetchone()
                    return f"Query termination result: {result[0]}" if result else "Query terminated"
        except Exception as e:
            return f"Error killing query: {str(e)}"

class ConnectionInfoTool(BaseTool):
    name: str = "connection_info_getter"
    description: str = "Get database connection information and active connections"
    
    def _run(self) -> str:
        try:
            db = DatabaseConnection()
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) as active_connections,
                               MAX(backend_start) as latest_connection
                        FROM pg_stat_activity
                        WHERE state = 'active'
                    """)
                    result = cur.fetchone()
                    return f"Active connections: {result[0]}, Latest: {result[1]}"
        except Exception as e:
            return f"Error getting connection info: {str(e)}"

class WeatherTool(BaseTool):
    name: str = "weather_checker"
    description: str = "Get current weather information (unrelated tool for testing)"
    
    def _run(self, city: str = "New York") -> str:
        # Mock weather data for testing tool selection
        return f"Weather in {city}: 72°F, Sunny"
