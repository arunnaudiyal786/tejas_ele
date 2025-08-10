#!/usr/bin/env python
"""
Example usage of the CrewAI Flow for query termination.
This script shows practical examples of how to use the flow system.
"""

from flow import kickoff_flow, create_query_termination_flow

def example_basic_usage():
    """Basic usage example with a ticket ID."""
    print("📋 Example 1: Basic Flow Usage with Ticket ID")
    print("-" * 50)
    
    # Simple way to run the flow
    result = kickoff_flow(ticket_id=1)
    
    if result['success']:
        print(f"✅ Flow completed successfully!")
        print(f"📊 Final State: {result['final_state']['final_status']}")
        print(f"📝 Result: {result['flow_result']}")
    else:
        print(f"❌ Flow failed: {result['error']}")
    
    print()

def example_advanced_usage():
    """Advanced usage with custom flow configuration."""
    print("🔧 Example 2: Advanced Flow Usage with Custom Configuration")
    print("-" * 50)
    
    # Create a custom flow instance
    flow = create_query_termination_flow(process_id=12345)
    
    # You can inspect the flow state before execution
    print(f"🔍 Flow state before execution:")
    print(f"   - Process ID: {flow.state.process_id}")
    print(f"   - Identifier Type: {flow.state.identifier_type}")
    print(f"   - Final Status: {flow.state.final_status}")
    
    # Execute the flow
    try:
        result = flow.kickoff()
        print(f"✅ Flow executed successfully!")
        print(f"📊 Final State: {flow.state.final_status}")
        print(f"📝 Result: {result}")
    except Exception as e:
        print(f"❌ Flow execution failed: {e}")
    
    print()

def example_batch_processing():
    """Example of processing multiple items with the flow."""
    print("🔄 Example 3: Batch Processing with Flow")
    print("-" * 50)
    
    # Process multiple tickets
    ticket_ids = [1, 2, 3, 4, 5]
    results = []
    
    for ticket_id in ticket_ids:
        print(f"🔄 Processing ticket {ticket_id}...")
        result = kickoff_flow(ticket_id=ticket_id)
        results.append(result)
        
        if result['success']:
            print(f"   ✅ Ticket {ticket_id} processed successfully")
        else:
            print(f"   ❌ Ticket {ticket_id} failed: {result['error']}")
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\n📊 Batch Processing Summary:")
    print(f"   - Total tickets: {len(ticket_ids)}")
    print(f"   - Successful: {successful}")
    print(f"   - Failed: {failed}")
    print()

def example_error_handling():
    """Example of error handling with the flow."""
    print("⚠️  Example 4: Error Handling with Flow")
    print("-" * 50)
    
    # Try to process with invalid parameters
    try:
        result = kickoff_flow()  # No parameters provided
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Caught exception: {e}")
    
    # Try to process with invalid identifier type
    try:
        # This would fail in the flow validation
        result = kickoff_flow(ticket_id=-1)  # Invalid ticket ID
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Caught exception: {e}")
    
    print()

def main():
    """Main function to run all examples."""
    print("🚀 CrewAI Flow Usage Examples")
    print("=" * 60)
    print()
    
    # Run examples
    example_basic_usage()
    example_advanced_usage()
    example_batch_processing()
    example_error_handling()
    
    print("🏁 All examples completed!")
    print("=" * 60)
    print()
    print("💡 Tips:")
    print("   - Use kickoff_flow() for simple execution")
    print("   - Use create_query_termination_flow() for custom configuration")
    print("   - The flow automatically handles state management")
    print("   - Check the final_state for detailed results")
    print("   - Use try-catch for error handling")

if __name__ == "__main__":
    main()
