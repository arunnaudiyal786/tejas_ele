import os
import sys
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from dotenv import load_dotenv
import yaml
from utils.pydantic_types import TicketAnalysis
from utils.helper import get_llm_config

# Add the backend directory to the Python path to access tools
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_dir)

# Load environment variables from .env file in the root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env'))


@CrewBase
class TicketAnalyzerCrew():
    """Crew for analyzing tickets and determining appropriate handlers"""
    
    def _load_yaml_config(self, file_name: str):
        """Load the config from the given path"""
        config_path = os.path.join(os.path.dirname(__file__), 'config', file_name)
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
        
    def __init__(self):
        self.agents_config = self._load_yaml_config('agents.yaml')
        self.tasks_config = self._load_yaml_config('tasks.yaml')
        self.llm_config = get_llm_config()



    @agent
    def ticket_analyzer(self) -> Agent:
        """Create ticket analyzer agent from config"""
        return Agent(
            config=self.agents_config['ticket_analyzer'],
            llm=self.llm_config,
            verbose=True
        )

    @task
    def analyze_ticket(self) -> Task:
        """Create a task to analyze ticket content from config"""

        ticket_content = """{ticket_content}"""
        return Task(            

            description = self.tasks_config['ticket_analysis']['description'].format(ticket_content=ticket_content),
            expected_output = self.tasks_config['ticket_analysis']['expected_output'],
            agent=self.ticket_analyzer(),
            output_pydantic=TicketAnalysis
            
            
        )

    @crew
    def crew(self) -> Crew:
        """Creates the TicketAnalyzer crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
