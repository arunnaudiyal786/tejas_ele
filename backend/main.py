import os
import datetime
import random
from dotenv import load_dotenv
from crewai.flow import Flow, listen, start, router , or_ , and_
from pydantic import BaseModel
from crews.db_agent.database_agent import DatabaseMonitoringCrew
from crews.ticket_analyzer.ticket_analyzer import TicketAnalyzerCrew
from crews.db_reasoning_crew.db_reasoning_crew import DatabaseComplexCrew

def generate_session_id():
    """Generate session_id in format: date_time_tillminutes_4_digit_random"""
    now = datetime.datetime.now()
    date_time = now.strftime("%Y%m%d_%H%M")
    random_num = random.randint(1000, 9999)
    return f"{date_time}_{random_num}"

def create_output_folder(session_id):
    """Create output folder for the session"""
    output_dir = f"results/{session_id}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

class DatabaseState(BaseModel):
    query_pid: int = 0
    status: str = ""
    action_result: str = ""
    crew_result: dict = {}
    ticket_route: str = ""
    ticket_content: str = ""
    session_id: str = ""

class DatabaseFlow(Flow[DatabaseState]):
    
    @start()
    def initialize_jira_automation_flow(self):
        """Initialize database monitoring flow"""
        print("🚀 Starting database monitoring flow...")
        self.state.session_id = generate_session_id()
        create_output_folder(self.state.session_id)
        print(f"📁 Session ID: {self.state.session_id}")
        return "Database monitoring initialized"
    

    @router(initialize_jira_automation_flow)
    def analyze_ticket(self):
        """Analyze the ticket"""
        print("🚀 Analyzing ticket...")

        with open("initial_files/ticket_description.txt", "r") as file:
            self.state.ticket_content = file.read()

        print("\n" + "="*60)
        print("📝 Ticket Content to Analyze:")
        print(self.state.ticket_content.strip())
        print("="*60 + "\n")


        ticket_analysis_crew = TicketAnalyzerCrew(session_id=self.state.session_id).crew()
        ticket_analysis_output = ticket_analysis_crew.kickoff(inputs={"ticket_content": self.state.ticket_content})

  
        self.state.ticket_route = ticket_analysis_output.pydantic.route_string
        print(f"\n🌈✨ Ticket route determined: [{self.state.ticket_route}] ✨🌈\n")

        if self.state.ticket_route == "database_crew":
            return "database_crew"
        elif self.state.ticket_route == "database_complex_crew":
            return "database_complex_crew"
        else:
            return "default_handler"
        



    
    @listen("database_crew")
    def execute_db_agent_crew(self):
        """Execute the database monitoring crew"""
        print("⚡ Executing database monitoring crew...")
        
        try:
            db_agent_crew = DatabaseMonitoringCrew(session_id=self.state.session_id).crew()
            db_agent_crew_output = db_agent_crew.kickoff()
            
            self.state.crew_result = db_agent_crew_output.raw
            self.state.status = "crew_executed"
            
            print("✅ Database monitoring crew executed successfully")
            return f"Crew execution completed: {db_agent_crew_output.raw}"
            
        except Exception as e:
            error_msg = f"Failed to execute database monitoring crew: {str(e)}"
            print(f"❌ {error_msg}")
            self.state.crew_result = {
                'success': False,
                'error': str(e)
            }
            raise Exception(error_msg)
        
    @listen("database_complex_crew")
    def execute_database_complex_crew(self):
        """Execute the database complex crew"""
        print("⚡ Executing database complex crew...")

        try:
            db_complex_crew = DatabaseComplexCrew(session_id=self.state.session_id).crew()
            db_complex_crew_output = db_complex_crew.kickoff()
            
            self.state.crew_result = db_complex_crew_output.raw
            self.state.status = "crew_executed"
            
            print("✅ Database complex crew executed successfully")
            return f"Crew execution completed: {db_complex_crew_output.raw}"
            
        except Exception as e:
            error_msg = f"Failed to execute database complex crew: {str(e)}"
            print(f"❌ {error_msg}")
            self.state.crew_result = {
                'success': False,
                'error': str(e)
            }
            raise Exception(error_msg)

        return "database_complex_crew"

    
    
    @listen(or_(execute_database_complex_crew, execute_db_agent_crew))
    def finalize_flow(self):
        """Finalize the database monitoring flow"""
        print("🏁 Finalizing database monitoring flow...")
        
        if self.state.crew_result:
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
