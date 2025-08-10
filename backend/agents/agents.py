"""
CrewAI Agent implementation for long-running query termination.
This module contains the agent logic for processing tickets and terminating problematic queries.
"""

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
import yaml
import os
from typing import Dict, Any

# Import custom tools
from .query_management_tool import (
    get_query_status,
    kill_query, 
    update_ticket_status,
    get_ticket_details
)

@CrewBase
class QueryTerminationCrew:
    """CrewAI implementation for query termination management."""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    @agent
    def query_termination_agent(self) -> Agent:
        """Create the query termination agent."""
        return Agent(
            config=self.agents_config['query_termination_agent'],
            tools=[
                get_query_status,
                kill_query,
                update_ticket_status,
                get_ticket_details
            ],
            verbose=True
        )
    
    @task
    def analyze_and_terminate_query(self) -> Task:
        """Create the main task for analyzing and terminating queries."""
        return Task(
            config=self.tasks_config['analyze_and_terminate_query'],
            agent=self.query_termination_agent()
        )
    
    @crew
    def crew(self) -> Crew:
        """Create the crew with the agent and task."""
        return Crew(
            agents=self.agents_config_data(),
            tasks=self.tasks_config_data(),
            process=Process.sequential,
            verbose=True
        )

class QueryTerminationAgent:
    """Main class for handling query termination requests."""
    
    def __init__(self):
        """Initialize the agent crew."""
        self.crew_instance = QueryTerminationCrew()
    
    def process_ticket(self, ticket_id: int, process_id: int = None) -> Dict[str, Any]:
        """
        Process a ticket for potential query termination.
        
        Args:
            ticket_id: The ticket ID to process
            process_id: Optional process ID if known directly
            
        Returns:
            Dict containing the processing results
        """
        try:
            # Prepare input for the crew
            inputs = {
                'ticket_id': ticket_id,
                'process_id': process_id
            }
            
            # Execute the crew
            result = self.crew_instance.crew().kickoff(inputs=inputs)
            
            return {
                'success': True,
                'ticket_id': ticket_id,
                'result': str(result),
                'message': 'Ticket processed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'ticket_id': ticket_id,
                'error': str(e),
                'message': f'Failed to process ticket {ticket_id}'
            }
    
    def process_ticket_by_id(self, identifier: int, identifier_type: str = 'ticket') -> Dict[str, Any]:
        """
        Process a ticket or query by different identifier types.
        
        Args:
            identifier: The ID (ticket_id, process_id, or query_id)
            identifier_type: Type of identifier ('ticket', 'process', 'query')
            
        Returns:
            Dict containing the processing results
        """
        if identifier_type == 'ticket':
            return self.process_ticket(identifier)
        
        elif identifier_type == 'process':
            # Find tickets associated with this process ID
            return self._process_by_process_id(identifier)
        
        elif identifier_type == 'query':
            # Find tickets associated with this query ID
            return self._process_by_query_id(identifier)
        
        else:
            return {
                'success': False,
                'error': f'Invalid identifier_type: {identifier_type}',
                'message': 'identifier_type must be "ticket", "process", or "query"'
            }
    
    def _process_by_process_id(self, process_id: int) -> Dict[str, Any]:
        """Find and process tickets associated with a process ID."""
        try:
            import sqlite3
            conn = sqlite3.connect("/Users/arunnaudiyal/Arun/Deloitte/Tejas/Code/tejas_ele/app_metadata.db")
            cursor = conn.cursor()
            
            # Find tickets associated with queries that have this process_id
            cursor.execute("""
                SELECT t.id FROM tickets t
                JOIN queries q ON t.query_id = q.id
                WHERE q.process_id = ? AND t.status = 'open'
            """, (process_id,))
            
            tickets = cursor.fetchall()
            conn.close()
            
            if not tickets:
                return {
                    'success': False,
                    'message': f'No open tickets found for process ID {process_id}',
                    'process_id': process_id
                }
            
            # Process the first matching ticket
            ticket_id = tickets[0][0]
            return self.process_ticket(ticket_id, process_id)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'process_id': process_id
            }
    
    def _process_by_query_id(self, query_id: int) -> Dict[str, Any]:
        """Find and process tickets associated with a query ID."""
        try:
            import sqlite3
            conn = sqlite3.connect("/Users/arunnaudiyal/Arun/Deloitte/Tejas/Code/tejas_ele/app_metadata.db")
            cursor = conn.cursor()
            
            # Find tickets for this query_id
            cursor.execute("""
                SELECT id FROM tickets 
                WHERE query_id = ? AND status = 'open'
            """, (query_id,))
            
            tickets = cursor.fetchall()
            conn.close()
            
            if not tickets:
                return {
                    'success': False,
                    'message': f'No open tickets found for query ID {query_id}',
                    'query_id': query_id
                }
            
            # Process the first matching ticket
            ticket_id = tickets[0][0]
            return self.process_ticket(ticket_id)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query_id': query_id
            }

# Convenience function for easy access
def create_query_termination_agent() -> QueryTerminationAgent:
    """Create and return a QueryTerminationAgent instance."""
    return QueryTerminationAgent()

# Main execution function
def handle_query_termination(identifier: int, identifier_type: str = 'ticket') -> Dict[str, Any]:
    """
    Main function to handle query termination requests.
    
    Args:
        identifier: The ID (ticket_id, process_id, or query_id)  
        identifier_type: Type of identifier ('ticket', 'process', 'query')
        
    Returns:
        Dict containing the processing results
    """
    agent = create_query_termination_agent()
    return agent.process_ticket_by_id(identifier, identifier_type)