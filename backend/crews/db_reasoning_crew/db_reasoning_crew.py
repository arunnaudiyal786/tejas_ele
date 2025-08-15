
import os
import sys
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from dotenv import load_dotenv
import yaml

# Add the backend directory to the Python path to access tools
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_dir)

# Load environment variables from .env file in the root directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env'))

from utils.pydantic_types import (
    MemberInsertionOutput, 
    ProviderInsertionOutput, 
    DuplicateDetectionOutput, 
    DuplicateCleanupOutput, 
    DataValidationOutput, 
    OrchestrationOutput,
    PlanningOutput
)
from utils.helper import get_llm_config
from tools.db_reasoning_tools import (
    MemberInsertionTool, 
    ProviderInsertionTool, 
    DuplicateDetectionTool, 
    DuplicateCleanupTool, 
    DataValidationTool
)

@CrewBase
class DatabaseComplexCrew:
    """Database complex reasoning crew for healthcare data management"""

    def _load_yaml_config(self, file_name: str):
        """Load the config from the given path"""
        config_path = os.path.join(os.path.dirname(__file__), 'config', file_name)
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
        
    def __init__(self):
        self.agents_config = self._load_yaml_config('agents.yaml')
        self.tasks_config = self._load_yaml_config('tasks.yaml')
        self.llm_config = get_llm_config()
        from crewai_tools import NL2SQLTool

        # psycopg2 was installed to run this example with PostgreSQL
        self.nl2sql = NL2SQLTool(db_uri="postgresql://testuser:testpass@localhost:5433/testdb")

    
    # @agent
    # def manager_agent(self) -> Agent:
    #     """Create database operations manager agent"""
    #     return Agent(
    #         config=self.agents_config['manager_agent'],
    #         llm=self.llm_config,
    #         verbose=True
    #     )
    
    @agent
    def data_insertion_agent(self) -> Agent:
        """Create data insertion specialist agent"""
        return Agent(
            config=self.agents_config['data_insertion_agent'],
            # tools=[MemberInsertionTool(), ProviderInsertionTool()],
            tools=[self.nl2sql],
            llm=self.llm_config,
            verbose=True
        )
    
    # @agent
    # def duplicate_detection_agent(self) -> Agent:
    #     """Create data quality analyst agent"""
    #     return Agent(
    #         config=self.agents_config['duplicate_detection_agent'],
    #         # tools=[DuplicateDetectionTool(), DuplicateCleanupTool()],
    #         tools=[self.nl2sql],
    #         llm=self.llm_config,
    #         verbose=True
    #     )
    
    @agent
    def db_report_generator_agent(self) -> Agent:
        """Create database report generator agent"""
        return Agent(
            config=self.agents_config['db_report_generator_agent'],
            llm=self.llm_config,
            verbose=True
        )
    
    # @agent
    # def data_validation_agent(self) -> Agent:
    #     """Create data validation specialist agent"""
    #     return Agent(
    #         config=self.agents_config['data_validation_agent'],
    #         # tools=[DataValidationTool()],
    #         tools=[self.nl2sql],
    #         llm=self.llm_config,
    #         verbose=True
    #     )
    
    # @task
    # def planning_task(self) -> Task:
    #     """Create task for planning the database operations"""
    #     return Task(
    #         config=self.tasks_config['planning_task'],
    #         agent=self.manager_agent(),
    #         output_pydantic=PlanningOutput
    #     )
    
    @task
    def member_insertion_task(self) -> Task:
        """Create task for inserting new member enrollment records"""
        return Task(
            config=self.tasks_config['member_insertion_task'],
            agent=self.data_insertion_agent(),
            output_pydantic=MemberInsertionOutput
        )
    
    @task
    def provider_insertion_task(self) -> Task:
        """Create task for inserting new provider records"""
        return Task(
            config=self.tasks_config['provider_insertion_task'],
            agent=self.data_insertion_agent(),
            output_pydantic=ProviderInsertionOutput
        )
    
    # @task
    # def duplicate_detection_task(self) -> Task:
    #     """Create task for detecting duplicate records"""
    #     return Task(
    #         config=self.tasks_config['duplicate_detection_task'],
    #         agent=self.duplicate_detection_agent(),
    #         output_pydantic=DuplicateDetectionOutput
    #     )
    
    # @task
    # def duplicate_cleanup_task(self) -> Task:
    #     """Create task for cleaning up duplicate records"""
    #     context = [self.duplicate_detection_task()]
    #     return Task(
    #         config=self.tasks_config['duplicate_cleanup_task'],
    #         agent=self.duplicate_detection_agent(),
    #         context=context,
    #         output_pydantic=DuplicateCleanupOutput
    #     )
    
    # @task
    # def data_validation_task(self) -> Task:
    #     """Create task for validating data integrity"""
    #     context = [
    #         self.member_insertion_task(), 
    #         self.provider_insertion_task(), 
    #         self.duplicate_cleanup_task()
    #     ]
    #     return Task(
    #         config=self.tasks_config['data_validation_task'],
    #         agent=self.data_validation_agent(),
    #         context=context,
    #         output_pydantic=DataValidationOutput
    #     )
    
    @task
    def orchestration_task(self) -> Task:
        """Create orchestration task for managing overall workflow"""
        context = [
            # self.planning_task(),
            self.member_insertion_task(),
            self.provider_insertion_task(),
            # self.duplicate_detection_task(),
            # self.duplicate_cleanup_task(),
            # self.data_validation_task()
        ]
        return Task(
            config=self.tasks_config['orchestration_task'],
            agent=self.db_report_generator_agent(),
            context=context,
            output_pydantic=OrchestrationOutput,
            output_file=os.path.join("orchestration_results.json")
        )
    
    @crew
    def crew(self) -> Crew:
        """Create a crew for database complex reasoning tasks"""
        return Crew(
            # agents=[self.data_insertion_agent(), self.duplicate_detection_agent()],
            # tasks=[self.planning_task(), self.member_insertion_task(), self.provider_insertion_task(), self.duplicate_detection_task(), self.duplicate_cleanup_task(), self.orchestration_task()],
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            # manager_agent=self.manager_agent(),
            verbose=True
            
        )