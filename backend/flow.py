#!/usr/bin/env python
"""
CrewAI Flow implementation for query termination management.
This module uses the Flow class with @start and @listen decorators to orchestrate
the query termination process using the QueryTerminationCrew.
"""

from pydantic import BaseModel
from crewai.flow.flow import Flow, listen, start
from typing import Dict, Any, Optional
from .agents.agents import QueryTerminationCrew

class QueryTerminationState(BaseModel):
    """State management for the query termination flow."""
    ticket_id: Optional[int] = None
    process_id: Optional[int] = None
    query_id: Optional[int] = None
    identifier_type: str = "ticket"
    ticket_details: Dict[str, Any] = {}
    query_status: Dict[str, Any] = {}
    termination_result: Dict[str, Any] = {}
    final_status: str = "pending"

class QueryTerminationFlow(Flow[QueryTerminationState]):
    """Flow for managing query termination requests."""
    
    def __init__(self):
        """Initialize the flow with the query termination crew."""
        super().__init__()
        self.crew_instance = QueryTerminationCrew()
    
    @start()
    def initialize_flow(self):
        """Initialize the flow with input parameters."""
        print("🚀 Starting Query Termination Flow")
        
        # In a real application, these would come from user input or API call
        # For now, we'll set default values that can be overridden
        if not self.state.ticket_id and not self.state.process_id and not self.state.query_id:
            print("⚠️  No identifiers provided, using default ticket ID 1")
            self.state.ticket_id = 1
            self.state.identifier_type = "ticket"
        
        print(f"📋 Flow initialized for {self.state.identifier_type}: {self.state.ticket_id or self.state.process_id or self.state.query_id}")
        return f"Flow initialized for {self.state.identifier_type}"
    
    @listen(initialize_flow)
    def validate_inputs(self):
        """Validate the input parameters and determine the processing approach."""
        print("🔍 Validating input parameters...")
        
        if self.state.ticket_id:
            self.state.identifier_type = "ticket"
            print(f"✅ Processing by ticket ID: {self.state.ticket_id}")
        elif self.state.process_id:
            self.state.identifier_type = "process"
            print(f"✅ Processing by process ID: {self.state.process_id}")
        elif self.state.query_id:
            self.state.identifier_type = "query"
            print(f"✅ Processing by query ID: {self.state.query_id}")
        else:
            raise ValueError("No valid identifier provided")
        
        return f"Input validation completed for {self.state.identifier_type}"
    
    @listen(validate_inputs)
    def execute_query_termination(self):
        """Execute the query termination using the CrewAI crew."""
        print("⚡ Executing query termination with CrewAI crew...")
        
        try:
            # Prepare inputs for the crew
            inputs = {}
            if self.state.ticket_id:
                inputs['ticket_id'] = self.state.ticket_id
            if self.state.process_id:
                inputs['process_id'] = self.state.process_id
            if self.state.query_id:
                inputs['query_id'] = self.state.query_id
            
            # Execute the crew
            result = self.crew_instance.crew().kickoff(inputs=inputs)
            
            # Store the result in state
            self.state.termination_result = {
                'success': True,
                'result': str(result),
                'raw_result': result
            }
            
            print("✅ Query termination executed successfully")
            return "Query termination completed successfully"
            
        except Exception as e:
            error_msg = f"Failed to execute query termination: {str(e)}"
            print(f"❌ {error_msg}")
            self.state.termination_result = {
                'success': False,
                'error': str(e)
            }
            raise Exception(error_msg)
    
    @listen(execute_query_termination)
    def finalize_flow(self):
        """Finalize the flow and update final status."""
        print("🏁 Finalizing query termination flow...")
        
        if self.state.termination_result.get('success'):
            self.state.final_status = "completed"
            print("✅ Flow completed successfully")
        else:
            self.state.final_status = "failed"
            print("❌ Flow failed")
        
        return f"Flow finalized with status: {self.state.final_status}"

def create_query_termination_flow(
    ticket_id: Optional[int] = None,
    process_id: Optional[int] = None,
    query_id: Optional[int] = None
) -> QueryTerminationFlow:
    """
    Create a QueryTerminationFlow instance with the specified parameters.
    
    Args:
        ticket_id: Optional ticket ID to process
        process_id: Optional process ID to process
        query_id: Optional query ID to process
        
    Returns:
        Configured QueryTerminationFlow instance
    """
    flow = QueryTerminationFlow()
    
    # Set the state based on provided parameters
    if ticket_id:
        flow.state.ticket_id = ticket_id
    if process_id:
        flow.state.process_id = process_id
    if query_id:
        flow.state.query_id = query_id
    
    return flow

def kickoff_flow(
    ticket_id: Optional[int] = None,
    process_id: Optional[int] = None,
    query_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Kickoff the query termination flow.
    
    Args:
        ticket_id: Optional ticket ID to process
        process_id: Optional process ID to process
        query_id: Optional query ID to process
        
    Returns:
        Dict containing the flow execution results
    """
    try:
        flow = create_query_termination_flow(ticket_id, process_id, query_id)
        result = flow.kickoff()
        
        return {
            'success': True,
            'flow_result': result,
            'final_state': flow.state.dict(),
            'message': 'Flow executed successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Flow execution failed'
        }

def plot_flow():
    """Generate a visual plot of the flow."""
    flow = QueryTerminationFlow()
    flow.plot("QueryTerminationFlowPlot")
    print("📊 Flow plot generated as QueryTerminationFlowPlot")

if __name__ == "__main__":
    # Example usage
    print("🚀 Starting Query Termination Flow Example")
    
    # Run the flow
    result = kickoff_flow(ticket_id=1)
    print(f"Flow Result: {result}")
    
    # Generate flow plot
    plot_flow()
