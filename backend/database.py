"""
Database operations for long-running query management system.
Handles both PostgreSQL (main data) and SQLite (metadata) operations.
"""

import sqlite3
import psycopg2
import asyncio
import asyncpg
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
import json
import os
from contextlib import asynccontextmanager

# PostgreSQL connection parameters
PG_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'longquery_demo'),
    'user': os.getenv('DB_USER', 'arunnaudiyal'),  # Use current macOS user
    'password': os.getenv('DB_PASSWORD', ''),  # No password needed for local macOS user
    'port': int(os.getenv('DB_PORT', '5432'))
}

# SQLite database path
SQLITE_DB = os.path.join(os.getenv('SQLITE_PATH', '.'), 'app_metadata.db')

class DatabaseManager:
    def __init__(self):
        self.pg_pool = None
        self.setup_sqlite()
    
    async def setup_postgresql_pool(self):
        """Initialize PostgreSQL connection pool."""
        try:
            self.pg_pool = await asyncpg.create_pool(
                host=PG_CONFIG['host'],
                database=PG_CONFIG['database'],
                user=PG_CONFIG['user'],
                password=PG_CONFIG['password'],
                port=PG_CONFIG['port'],
                min_size=5,
                max_size=20
            )
            return True
        except Exception as e:
            print(f"Failed to setup PostgreSQL pool: {e}")
            return False
    
    def setup_sqlite(self):
        """Initialize SQLite database for metadata."""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        # Create queries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                query_name VARCHAR(200),
                pg_session_pid INTEGER,
                status VARCHAR(20) DEFAULT 'running',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                result_rows INTEGER,
                error_message TEXT
            )
        ''')
        
        # Create tickets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER,
                description TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolution_details TEXT,
                FOREIGN KEY (query_id) REFERENCES queries (id)
            )
        ''')
        
        # Create sessions table for tracking active PostgreSQL sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER,
                pid INTEGER UNIQUE,
                query_start TIMESTAMP,
                application_name VARCHAR(100),
                client_addr VARCHAR(50),
                state VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES queries (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_query_metadata(self, query_text: str, query_name: str = None, pg_session_pid: int = None) -> int:
        """Save query metadata to SQLite and return query ID."""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO queries (query_text, query_name, pg_session_pid, status)
            VALUES (?, ?, ?, 'running')
        ''', (query_text, query_name, pg_session_pid))
        
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return query_id
    
    def update_query_status(self, query_id: int, status: str, result_rows: int = None, error_message: str = None):
        """Update query status in SQLite."""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        if status == 'completed' or status == 'terminated' or status == 'error':
            cursor.execute('''
                UPDATE queries 
                SET status = ?, completed_at = CURRENT_TIMESTAMP, result_rows = ?, error_message = ?
                WHERE id = ?
            ''', (status, result_rows, error_message, query_id))
        else:
            cursor.execute('UPDATE queries SET status = ? WHERE id = ?', (status, query_id))
        
        conn.commit()
        conn.close()
    
    def create_ticket(self, query_id: int, description: str) -> int:
        """Create a new ticket for a query."""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tickets (query_id, description, status)
            VALUES (?, ?, 'open')
        ''', (query_id, description))
        
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ticket_id
    
    def get_open_tickets(self) -> List[Dict]:
        """Get all open tickets."""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.id, t.query_id, t.description, t.created_at, 
                   q.query_text, q.query_name, q.pg_session_pid, q.status
            FROM tickets t
            JOIN queries q ON t.query_id = q.id
            WHERE t.status = 'open' AND q.status = 'running'
            ORDER BY t.created_at ASC
        ''')
        
        tickets = []
        for row in cursor.fetchall():
            tickets.append({
                'ticket_id': row[0],
                'query_id': row[1],
                'description': row[2],
                'created_at': row[3],
                'query_text': row[4],
                'query_name': row[5],
                'pg_session_pid': row[6],
                'query_status': row[7]
            })
        
        conn.close()
        return tickets
    
    def resolve_ticket(self, ticket_id: int, resolution_details: str):
        """Mark a ticket as resolved."""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tickets 
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP, resolution_details = ?
            WHERE id = ?
        ''', (resolution_details, ticket_id))
        
        conn.commit()
        conn.close()
    
    def get_all_queries(self) -> List[Dict]:
        """Get all queries with their current status."""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, query_text, query_name, pg_session_pid, status, 
                   created_at, completed_at, result_rows, error_message
            FROM queries
            ORDER BY created_at DESC
        ''')
        
        queries = []
        for row in cursor.fetchall():
            queries.append({
                'id': row[0],
                'query_text': row[1],
                'query_name': row[2],
                'pg_session_pid': row[3],
                'status': row[4],
                'created_at': row[5],
                'completed_at': row[6],
                'result_rows': row[7],
                'error_message': row[8]
            })
        
        conn.close()
        return queries
    
    def get_all_tickets(self) -> List[Dict]:
        """Get all tickets."""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.id, t.query_id, t.description, t.status, 
                   t.created_at, t.resolved_at, t.resolution_details,
                   q.query_name, q.status as query_status
            FROM tickets t
            JOIN queries q ON t.query_id = q.id
            ORDER BY t.created_at DESC
        ''')
        
        tickets = []
        for row in cursor.fetchall():
            tickets.append({
                'ticket_id': row[0],
                'query_id': row[1],
                'description': row[2],
                'status': row[3],
                'created_at': row[4],
                'resolved_at': row[5],
                'resolution_details': row[6],
                'query_name': row[7],
                'query_status': row[8]
            })
        
        conn.close()
        return tickets
    
    async def execute_query_async(self, query_text: str, query_name: str = None) -> Dict:
        """Execute a PostgreSQL query asynchronously and track the session."""
        if not self.pg_pool:
            await self.setup_postgresql_pool()
        
        # Save query metadata first
        query_id = self.save_query_metadata(query_text, query_name)
        
        try:
            async with self.pg_pool.acquire() as conn:
                # Get the backend PID for this connection
                pid_result = await conn.fetchrow("SELECT pg_backend_pid()")
                pg_session_pid = pid_result['pg_backend_pid']
                
                # Update query metadata with PID
                conn_sqlite = sqlite3.connect(SQLITE_DB)
                cursor = conn_sqlite.cursor()
                cursor.execute('UPDATE queries SET pg_session_pid = ? WHERE id = ?', (pg_session_pid, query_id))
                conn_sqlite.commit()
                conn_sqlite.close()
                
                # Execute the actual query
                start_time = datetime.now()
                result = await conn.fetch(query_text)
                end_time = datetime.now()
                
                # Update status to completed
                execution_time = (end_time - start_time).total_seconds()
                self.update_query_status(query_id, 'completed', len(result))
                
                return {
                    'query_id': query_id,
                    'status': 'completed',
                    'rows': len(result),
                    'execution_time': execution_time,
                    'pg_session_pid': pg_session_pid,
                    'data': [dict(row) for row in result[:100]]  # Return first 100 rows
                }
                
        except Exception as e:
            self.update_query_status(query_id, 'error', error_message=str(e))
            return {
                'query_id': query_id,
                'status': 'error',
                'error': str(e)
            }
    
    async def get_active_pg_sessions(self) -> List[Dict]:
        """Get active PostgreSQL sessions."""
        if not self.pg_pool:
            await self.setup_postgresql_pool()
        
        try:
            async with self.pg_pool.acquire() as conn:
                result = await conn.fetch('''
                    SELECT 
                        pid,
                        application_name,
                        client_addr,
                        query_start,
                        state,
                        query
                    FROM pg_stat_activity 
                    WHERE state = 'active' 
                        AND pid != pg_backend_pid()
                        AND query NOT LIKE '%pg_stat_activity%'
                    ORDER BY query_start
                ''')
                
                sessions = []
                for row in result:
                    sessions.append({
                        'pid': row['pid'],
                        'application_name': row['application_name'],
                        'client_addr': row['client_addr'],
                        'query_start': row['query_start'].isoformat() if row['query_start'] else None,
                        'state': row['state'],
                        'query': row['query'][:200] + '...' if len(row['query']) > 200 else row['query']
                    })
                
                return sessions
                
        except Exception as e:
            print(f"Error getting active sessions: {e}")
            return []
    
    async def terminate_pg_session(self, pid: int) -> Dict:
        """Terminate a PostgreSQL session by PID."""
        if not self.pg_pool:
            await self.setup_postgresql_pool()
        
        try:
            async with self.pg_pool.acquire() as conn:
                # First check if the session exists
                session_check = await conn.fetchrow(
                    "SELECT pid, state, query FROM pg_stat_activity WHERE pid = $1", pid
                )
                
                if not session_check:
                    return {'success': False, 'message': f'Session with PID {pid} not found'}
                
                # Terminate the session
                result = await conn.fetchrow("SELECT pg_terminate_backend($1) as terminated", pid)
                
                if result['terminated']:
                    # Update any associated queries
                    conn_sqlite = sqlite3.connect(SQLITE_DB)
                    cursor = conn_sqlite.cursor()
                    cursor.execute(
                        'UPDATE queries SET status = ? WHERE pg_session_pid = ? AND status = ?',
                        ('terminated', pid, 'running')
                    )
                    conn_sqlite.commit()
                    conn_sqlite.close()
                    
                    return {
                        'success': True, 
                        'message': f'Successfully terminated session {pid}',
                        'session_info': dict(session_check)
                    }
                else:
                    return {'success': False, 'message': f'Failed to terminate session {pid}'}
                    
        except Exception as e:
            return {'success': False, 'message': f'Error terminating session: {str(e)}'}

# Global database manager instance
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager