import os
import sys
from crewai import Agent, Task, Crew
from crewai.project import CrewBase, agent, task, crew
from dotenv import load_dotenv
import yaml

# Add the backend directory to the Python path to access tools
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_dir)

# Load environment variables from .env file in the root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env'))

from utils.pydantic_types import QueryResolutionOutput
from utils.helper import get_llm_config
from tools.database_tools import QueryStatusTool, QueryKillerTool, ConnectionInfoTool, WeatherTool

@CrewBase
class DatabaseMonitoringCrew:
    """Database monitoring crew for PostgreSQL operations"""

    def _load_yaml_config(self, file_name: str):
        """Load the config from the given path"""
        config_path = os.path.join(os.path.dirname(__file__), 'config', file_name)
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
        
    def __init__(self, session_id=None):
        self.agents_config = self._load_yaml_config('agents.yaml')
        self.tasks_config = self._load_yaml_config('tasks.yaml')
        self.llm_config = get_llm_config()
        self.session_id = session_id
        if self.session_id:
            self.output_dir = f"results/{self.session_id}"
            os.makedirs(self.output_dir, exist_ok=True)
    
    @agent
    def database_administrator(self) -> Agent:
        """Create database administrator agent from config"""
        return Agent(
            config=self.agents_config['database_administrator'],
            tools=[QueryStatusTool(), QueryKillerTool(), WeatherTool()],
            llm=self.llm_config,
            verbose=True
        )
    
    @task
    def query_status_check(self) -> Task:
        """Create a task to check the status of database queries"""
        return Task(
            config=self.tasks_config['query_status_check'],
            expected_output=self.tasks_config['query_status_check']['expected_output'],
            output_pydantic=QueryResolutionOutput,
            agent=self.database_administrator()
        )
    
    @task
    def connection_info_check(self) -> Task:
        """Create a task to get database connection information"""
        return Task(
            config=self.tasks_config['connection_info_check'],
            agent=self.database_administrator()
        )
    
    @task
    def query_resolution(self) -> Task:
        """Create a task to manage queries based on status"""

        context = [self.query_status_check(), self.connection_info_check()]
        
        output_file = os.path.join(self.output_dir, "query_resolution.json") if self.session_id else "query_resolution.json"

        return Task(
            config=self.tasks_config['query_resolution'],
            agent=self.database_administrator(),
            context=context,
            expected_output=self.tasks_config['query_resolution']['expected_output'],
            output_pydantic=QueryResolutionOutput,
            output_file=output_file
        )
    
    @crew
    def crew(self) -> Crew:
        """Create a crew for database monitoring tasks"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            cache=False
        )
