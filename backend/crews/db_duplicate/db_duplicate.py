import os
import sys
from crewai import Agent, Task, Crew
from crewai.project import CrewBase, agent, task, crew
from dotenv import load_dotenv

# Add the backend directory to the Python path to access tools
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_dir)

# Load environment variables from .env file in the root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env'))

from tools.db_duplicate_tools import DBDuplicateCheckerTicketParserTool, DBDuplicateCheckerDuplicateDetectorTool, DBDuplicateQueryExecutor

@CrewBase
class DuplicateAnalysisCrew:
    """Crew for analyzing tickets and detecting database duplicates"""
    
    @agent
    def duplicate_analyst(self) -> Agent:
        """Create duplicate analyst agent from config"""
        return Agent(
            config=self.agents_config['duplicate_analyst'],
            tools=[DBDuplicateCheckerTicketParserTool(), DBDuplicateCheckerDuplicateDetectorTool(), DBDuplicateQueryExecutor()],
            verbose=True
        )

    @task
    def ticket_analysis(self) -> Task:
        """Create a task to analyze ticket information from config"""
        return Task(
            config=self.tasks_config['ticket_analysis'],
            agent=self.duplicate_analyst()
        )

    @task
    def duplicate_detection(self) -> Task:
        """Create a task to detect duplicates from config"""
        return Task(
            config=self.tasks_config['duplicate_detection'],
            agent=self.duplicate_analyst()
        )

    @task
    def duplicate_resolution(self) -> Task:
        """Create a task for duplicate resolution from config"""
        return Task(
            config=self.tasks_config['duplicate_resolution'],
            agent=self.duplicate_analyst()
        )

    @task
    def duplicate_resolution_execution(self) -> Task:
        """Create a task for duplicate resolution execution from config"""
        return Task(
            config=self.tasks_config['duplicate_resolution_execution'],
            agent=self.duplicate_analyst()
        )

    @crew
    def crew(self) -> Crew:
        """Create a crew for duplicate analysis tasks"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True
        )

def execute_duplicate_analysis(ticket_content: str = "Analyze duplicates in users table by email field") -> dict:
    """Execute the duplicate analysis crew and return results"""
    crew_instance = DuplicateAnalysisCrew()
    
    inputs = {'ticket_content': ticket_content}
    result = crew_instance.crew().kickoff(inputs=inputs)
    
    return {
        'success': True,
        'result': str(result),
        'raw_result': result
    }