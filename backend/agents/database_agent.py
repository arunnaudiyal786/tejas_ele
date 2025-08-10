from crewai import Agent, Task, Crew
from tools.database_tools import QueryStatusTool, QueryKillerTool, ConnectionInfoTool, WeatherTool

database_agent = Agent(
    role="Database Administrator",
    goal="Monitor and manage database queries efficiently",
    backstory="Expert DBA with deep knowledge of PostgreSQL operations and query optimization",
    verbose=True,
    allow_delegation=False
)

def create_query_status_task() -> Task:
    """Create a task to check the status of database queries."""
    return Task(
        description="Check the status of database queries, particularly looking for long-running ones",
        agent=database_agent,
        expected_output="Status report of active database queries",
        tools=[QueryStatusTool()]
    )

def create_connection_info_task() -> Task:
    """Create a task to get database connection information."""
    return Task(
        description="Get current database connection information and statistics",
        agent=database_agent,
        expected_output="Database connection statistics and information",
        tools=[ConnectionInfoTool()]
    )

def create_query_management_task() -> Task:
    """Create a task to manage queries based on status."""
    return Task(
        description="If there are problematic long-running queries, consider terminating them. Use your judgment.",
        agent=database_agent,
        expected_output="Query management action taken or recommendation",
        tools=[QueryKillerTool()]
    )

def create_database_monitoring_crew() -> Crew:
    """Create a crew for database monitoring tasks."""
    tasks = [
        create_query_status_task(),
        create_connection_info_task(),
        create_query_management_task()
    ]
    
    return Crew(
        agents=[database_agent],
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
