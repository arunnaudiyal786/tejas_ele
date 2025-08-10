#!/usr/bin/env python
"""
Test script for the CrewAI Flow implementation.
This script demonstrates how to use the QueryTerminationFlow with different parameters.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flow import (
    create_query_termination_flow,
    kickoff_flow,
    plot_flow,
    QueryTerminationFlow
)

def test_flow_with_ticket_id():
    """Test the flow with a ticket ID."""
    print("\n" + "="*50)
    print("🧪 Testing Flow with Ticket ID")
    print("="*50)
    
    try:
        result = kickoff_flow(ticket_id=1)
        print(f"✅ Flow Result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_flow_with_process_id():
    """Test the flow with a process ID."""
    print("\n" + "="*50)
    print("🧪 Testing Flow with Process ID")
    print("="*50)
    
    try:
        result = kickoff_flow(process_id=12345)
        print(f"✅ Flow Result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_flow_with_query_id():
    """Test the flow with a query ID."""
    print("\n" + "="*50)
    print("🧪 Testing Flow with Query ID")
    print("="*50)
    
    try:
        result = kickoff_flow(query_id=67890)
        print(f"✅ Flow Result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_flow_creation():
    """Test creating and configuring a flow instance."""
    print("\n" + "="*50)
    print("🧪 Testing Flow Creation")
    print("="*50)
    
    try:
        # Create flow with ticket ID
        flow = create_query_termination_flow(ticket_id=999)
        print(f"✅ Flow created with ticket ID: {flow.state.ticket_id}")
        
        # Create flow with process ID
        flow = create_query_termination_flow(process_id=888)
        print(f"✅ Flow created with process ID: {flow.state.process_id}")
        
        # Create flow with query ID
        flow = create_query_termination_flow(query_id=777)
        print(f"✅ Flow created with query ID: {flow.state.query_id}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_flow_plot():
    """Test generating a flow plot."""
    print("\n" + "="*50)
    print("🧪 Testing Flow Plot Generation")
    print("="*50)
    
    try:
        plot_flow()
        print("✅ Flow plot generated successfully")
        return True
    except Exception as e:
        print(f"❌ Error generating plot: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Starting CrewAI Flow Tests")
    print("="*50)
    
    # Test flow creation
    test_flow_creation()
    
    # Test flow execution with different parameters
    test_flow_with_ticket_id()
    test_flow_with_process_id()
    test_flow_with_query_id()
    
    # Test flow plotting
    test_flow_plot()
    
    print("\n" + "="*50)
    print("🏁 All tests completed!")
    print("="*50)

if __name__ == "__main__":
    main()
