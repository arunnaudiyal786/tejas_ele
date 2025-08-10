"""
Test script for the CrewAI query termination agent.
This script tests the agent functionality without requiring the full system to be running.
"""

import sys
import sqlite3
from datetime import datetime

# Add the backend directory to the path so we can import our modules
sys.path.append('.')

def create_test_data():
    """Create some test data for testing the agent."""
    print("Creating test data...")
    
    try:
        # Connect to SQLite metadata database
        conn = sqlite3.connect("/Users/arunnaudiyal/Arun/Deloitte/Tejas/Code/tejas_ele/app_metadata.db")
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT,
                status TEXT DEFAULT 'running',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                process_id INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'open'
            )
        """)
        
        # Insert test query
        cursor.execute(
            "INSERT INTO queries (query_text, process_id) VALUES (?, ?)",
            ("SELECT * FROM large_table WHERE complex_condition = true", 12345)
        )
        query_id = cursor.lastrowid
        
        # Insert test ticket
        cursor.execute(
            "INSERT INTO tickets (query_id, description) VALUES (?, ?)",
            (query_id, "Long running query is causing performance issues and needs to be terminated")
        )
        ticket_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print(f"Created test query with ID: {query_id}")
        print(f"Created test ticket with ID: {ticket_id}")
        return query_id, ticket_id
        
    except Exception as e:
        print(f"Error creating test data: {e}")
        return None, None

def test_tools():
    """Test the individual tools without the full agent."""
    print("\n" + "="*50)
    print("Testing Individual Tools")
    print("="*50)
    
    try:
        from agents.query_management_tool import (
            get_ticket_details, 
            update_ticket_status
        )
        
        # Get test data
        query_id, ticket_id = create_test_data()
        if not ticket_id:
            print("Failed to create test data")
            return False
        
        # Test get_ticket_details
        print(f"\n1. Testing get_ticket_details for ticket {ticket_id}...")
        result = get_ticket_details(ticket_id)
        print(f"Result: {result}")
        
        # Test update_ticket_status
        print(f"\n2. Testing update_ticket_status for ticket {ticket_id}...")
        result = update_ticket_status(
            ticket_id, 
            "resolved", 
            "Query termination test completed successfully"
        )
        print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"Error testing tools: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent():
    """Test the full agent workflow."""
    print("\n" + "="*50)
    print("Testing Full Agent Workflow")
    print("="*50)
    
    try:
        from flow import terminate_query_sync
        
        # Get test data
        query_id, ticket_id = create_test_data()
        if not ticket_id:
            print("Failed to create test data")
            return False
        
        print(f"\nTesting agent with ticket ID: {ticket_id}")
        result = terminate_query_sync(ticket_id, 'ticket')
        print(f"Agent result: {result}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"Error testing agent: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Query Termination Agent Test Suite")
    print("=" * 50)
    
    print("Note: This test requires:")
    print("1. CrewAI dependencies installed (crewai, crewai-tools)")
    print("2. OpenAI API key set in environment")
    print("3. PostgreSQL database accessible")
    print("\n" + "="*50)
    
    # Test tools first
    tools_success = test_tools()
    
    if not tools_success:
        print("\n❌ Tools test failed - skipping agent test")
        return
    
    # Test full agent workflow
    agent_success = test_agent()
    
    print("\n" + "="*50)
    print("Test Results Summary")
    print("="*50)
    print(f"Tools test: {'✅ PASSED' if tools_success else '❌ FAILED'}")
    print(f"Agent test: {'✅ PASSED' if agent_success else '❌ FAILED'}")
    
    if tools_success and agent_success:
        print("\n🎉 All tests passed! The agent is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()