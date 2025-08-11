import yaml
import os
import sys
from crewai import Agent, Task, Crew
from crewai.project import agent, task
from dotenv import load_dotenv

# Add the backend directory to the Python path to access tools
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_dir)

# Load environment variables from .env file in the root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env'))

from tools.database_tools import QueryStatusTool, QueryKillerTool, ConnectionInfoTool, WeatherTool

def load_config(config_file: str) -> dict:
    """Load configuration from YAML file"""
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, config_file)
    
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

# Load configurations
agents_config = load_config('config/agents.yaml')
tasks_config = load_config('config/tasks.yaml')

@agent
def database_administrator() -> Agent:
    """Create database administrator agent from YAML config"""
    config = agents_config['database_administrator']
    return Agent(
        role=config['role'],
        goal=config['goal'],
        backstory=config['backstory'],
        verbose=config['verbose'],
        allow_delegation=config['allow_delegation'],
        llm_config={
            "config_list": [{
                "model": "gpt-4",
                "api_key": os.getenv('OPENAI_API_KEY')
            }]
        }
    )

@task
def query_status_check() -> Task:
    """Create a task to check the status of database queries."""
    config = tasks_config['query_status_check']
    return Task(
        description=config['description'],
        agent=database_administrator(),
        expected_output=config['expected_output'],
        tools=[QueryStatusTool()]
    )

@task
def connection_info_check() -> Task:
    """Create a task to get database connection information."""
    config = tasks_config['connection_info_check']
    return Task(
        description=config['description'],
        agent=database_administrator(),
        expected_output=config['expected_output'],
        tools=[ConnectionInfoTool()]
    )

@task
def query_management() -> Task:
    """Create a task to manage queries based on status."""
    config = tasks_config['query_management']
    return Task(
        description=config['description'],
        agent=database_administrator(),
        expected_output=config['expected_output'],
        tools=[QueryKillerTool()]
    )

def create_database_monitoring_crew() -> Crew:
    """Create a crew for database monitoring tasks."""
    tasks = [
        query_status_check(),
        connection_info_check(),
        query_management()
    ]
    
    return Crew(
        agents=[database_administrator()],
        tasks=tasks,
        verbose=True
    )

def execute_database_monitoring() -> dict:
    """Execute the database monitoring crew and return results."""
    crew = create_database_monitoring_crew()
    result = crew.kickoff()
    
    return {
        'success': True,
        'result': str(result),
        'raw_result': result
    }
