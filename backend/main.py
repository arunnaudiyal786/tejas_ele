import os
from dotenv import load_dotenv
from crewai.flow import Flow, listen, start
from pydantic import BaseModel
from crews.db_agent.database_agent import create_database_monitoring_crew, execute_database_monitoring

class DatabaseState(BaseModel):
    query_pid: int = 0
    status: str = ""
    action_result: str = ""
    crew_result: dict = {}

class DatabaseFlow(Flow[DatabaseState]):
    
    @start()
    def initialize_monitoring(self):
        """Initialize database monitoring flow"""
        print("🚀 Starting database monitoring flow...")
        return "Database monitoring initialized"
    
    @listen(initialize_monitoring)
    def execute_database_crew(self):
        """Execute the database monitoring crew"""
        print("⚡ Executing database monitoring crew...")
        
        try:
            # Execute the crew from database_agent.py
            result = execute_database_monitoring()
            
            # Store the crew result in state
            self.state.crew_result = result
            self.state.status = "crew_executed"
            
            print("✅ Database monitoring crew executed successfully")
            return f"Crew execution completed: {result['result']}"
            
        except Exception as e:
            error_msg = f"Failed to execute database monitoring crew: {str(e)}"
            print(f"❌ {error_msg}")
            self.state.crew_result = {
                'success': False,
                'error': str(e)
            }
            raise Exception(error_msg)
    
    @listen(execute_database_crew)
    def finalize_flow(self):
        """Finalize the database monitoring flow"""
        print("🏁 Finalizing database monitoring flow...")
        
        if self.state.crew_result.get('success'):
            self.state.action_result = "completed"
            print("✅ Flow completed successfully")
        else:
            self.state.action_result = "failed"
            print("❌ Flow failed")
        
        return f"Flow finalized with status: {self.state.action_result}"

def create_database_flow() -> DatabaseFlow:
    """Create a DatabaseFlow instance."""
    return DatabaseFlow()

def kickoff_database_flow() -> dict:
    """Kickoff the database monitoring flow."""
    try:
        flow = create_database_flow()
        result = flow.kickoff()
        
        return {
            'success': True,
            'flow_result': result,
            'final_state': flow.state.dict(),
            'message': 'Database monitoring flow executed successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Database monitoring flow execution failed'
        }

def plot_flow():
    """Generate a visual plot of the flow."""
    flow = create_database_flow()
    flow.plot("DatabaseFlowPlot")
    print("📊 Flow plot generated as DatabaseFlowPlot")

def main():
    """Main entry point for the database monitoring application"""
    print("🚀 Starting Database Monitoring Application")
    
    # Run the flow
    result = kickoff_database_flow()
    print(f"Flow Result: {result}")
    
    # Generate flow plot
    plot_flow()
    
    return result

if __name__ == "__main__":
    main()
