"""
Example usage of the Query Termination Agent.
This shows how to use the agent in different scenarios.
"""

from flow import terminate_query_sync, process_all_open_tickets

def example_1_terminate_by_ticket_id():
    """Example: Terminate query by ticket ID"""
    print("Example 1: Terminating query by ticket ID")
    print("-" * 40)
    
    ticket_id = 1  # Replace with actual ticket ID
    result = terminate_query_sync(ticket_id, 'ticket')
    
    print(f"Ticket ID: {ticket_id}")
    print(f"Success: {result.get('success', False)}")
    print(f"Message: {result.get('message', 'No message')}")
    if 'error' in result:
        print(f"Error: {result['error']}")
    print()

def example_2_terminate_by_process_id():
    """Example: Terminate query by PostgreSQL process ID"""
    print("Example 2: Terminating query by process ID")
    print("-" * 40)
    
    process_id = 12345  # Replace with actual PostgreSQL PID
    result = terminate_query_sync(process_id, 'process')
    
    print(f"Process ID: {process_id}")
    print(f"Success: {result.get('success', False)}")
    print(f"Message: {result.get('message', 'No message')}")
    if 'error' in result:
        print(f"Error: {result['error']}")
    print()

def example_3_terminate_by_query_id():
    """Example: Terminate query by query ID"""
    print("Example 3: Terminating query by query ID")
    print("-" * 40)
    
    query_id = 1  # Replace with actual query ID
    result = terminate_query_sync(query_id, 'query')
    
    print(f"Query ID: {query_id}")
    print(f"Success: {result.get('success', False)}")
    print(f"Message: {result.get('message', 'No message')}")
    if 'error' in result:
        print(f"Error: {result['error']}")
    print()

def example_4_process_all_open_tickets():
    """Example: Process all open tickets"""
    print("Example 4: Processing all open tickets")
    print("-" * 40)
    
    result = process_all_open_tickets()
    
    print(f"Success: {result.get('success', False)}")
    print(f"Total tickets: {result.get('total_tickets', 0)}")
    print(f"Processed count: {result.get('processed_count', 0)}")
    print(f"Message: {result.get('message', 'No message')}")
    
    if 'results' in result:
        for ticket_result in result['results']:
            ticket_id = ticket_result['ticket_id']
            processed = ticket_result['processed']
            print(f"  Ticket {ticket_id}: {'Processed' if processed else 'Skipped'}")
    print()

def main():
    """Run all examples"""
    print("Query Termination Agent - Usage Examples")
    print("=" * 50)
    print()
    
    # Run examples
    example_1_terminate_by_ticket_id()
    example_2_terminate_by_process_id()
    example_3_terminate_by_query_id()
    example_4_process_all_open_tickets()
    
    print("Notes:")
    print("- Make sure to replace the example IDs with actual values")
    print("- Ensure PostgreSQL database is running and accessible")
    print("- Set OPENAI_API_KEY environment variable for CrewAI agent")
    print("- The agent will only terminate queries that are actually problematic")

if __name__ == "__main__":
    main()