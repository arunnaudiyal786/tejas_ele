from typing import Dict, Any, Optional, List
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class TicketAnalysis(BaseModel):
    route_string: str = Field(description="The route identifier (word/phrase) that matches one of the available handlers, or 'default_handler' if no specific match is found.")

class DuplicateAnalysis(BaseModel):
    tables: List[str] = Field(description="The list of tables that need duplicate checking")
    fields: List[str] = Field(description="The list of fields that need duplicate checking")

class QueryResolutionOutput(BaseModel):
    query_status: str = Field(description="The status of the query")
    query_resolution: str = Field(description="The resolution of the query")
    query_resolution_reason: str = Field(description="The reason for the query resolution")
    query_resolution_action: str = Field(description="The action to be taken to resolve the query")


########### DB REASONING ###########





class DuplicateAnalysis(BaseModel):
    tables: List[str] = Field(description="The list of tables that need duplicate checking")
    fields: List[str] = Field(description="The list of fields that need duplicate checking")

class QueryResolutionOutput(BaseModel):
    query_status: str = Field(description="The status of the query")
    query_resolution: str = Field(description="The resolution of the query")
    query_resolution_reason: str = Field(description="The reason for the query resolution")
    query_resolution_action: str = Field(description="The action to be taken to resolve the query")

# New models for database complex reasoning
class MemberInsertionOutput(BaseModel):
    inserted_member_count: int = Field(description="Number of member records successfully inserted")
    inserted_member_ids: List[str] = Field(description="List of member IDs that were inserted")
    validation_status: str = Field(description="Status of validation checks for inserted members")
    error_details: Optional[str] = Field(description="Details of any errors encountered during insertion")
    foreign_key_validation: str = Field(description="Confirmation that all foreign key constraints are satisfied")

class ProviderInsertionOutput(BaseModel):
    inserted_provider_count: int = Field(description="Number of provider records successfully inserted")
    inserted_provider_ids: List[str] = Field(description="List of provider IDs that were inserted")
    npi_validation_status: str = Field(description="Status of NPI number validation and uniqueness checks")
    network_assignments: List[str] = Field(description="List of network and product assignments for inserted providers")
    credentialing_status: str = Field(description="Confirmation that all providers have completed credentialing requirements")

class DuplicateDetectionOutput(BaseModel):
    duplicate_groups_found: int = Field(description="Number of duplicate member groups identified")
    duplicate_member_details: List[Dict[str, Any]] = Field(description="Details of each duplicate group including member IDs and personal information")
    total_duplicate_records: int = Field(description="Total number of duplicate records identified")
    detection_criteria_used: str = Field(description="Criteria used for identifying duplicates (e.g., name, DOB)")
    recommended_actions: List[str] = Field(description="Recommended actions for resolving each duplicate group")

class DuplicateCleanupOutput(BaseModel):
    removed_duplicate_count: int = Field(description="Number of duplicate records successfully removed")
    preserved_record_count: int = Field(description="Number of original records preserved")
    preserved_member_ids: List[str] = Field(description="List of member IDs that were preserved (earliest enrollment)")
    removed_member_ids: List[str] = Field(description="List of member IDs that were removed as duplicates")
    referential_integrity_status: str = Field(description="Confirmation that referential integrity is maintained")

class DataValidationOutput(BaseModel):
    overall_validation_status: str = Field(description="Overall status of data validation (PASSED/FAILED/WARNING)")
    member_validation_results: Dict[str, Any] = Field(description="Results of member enrollment table validation")
    provider_validation_results: Dict[str, Any] = Field(description="Results of provider network table validation")
    duplicate_check_results: str = Field(description="Confirmation that no duplicate records remain")
    business_rules_compliance: str = Field(description="Status of business rules compliance validation")
    data_quality_score: Optional[float] = Field(description="Overall data quality score (0-100)")

class OrchestrationOutput(BaseModel):
    ticket_status: str = Field(description="Overall ticket completion status")
    completed_tasks: List[str] = Field(description="List of successfully completed tasks")
    task_execution_summary: Dict[str, str] = Field(description="Summary of each task execution with results")
    issues_encountered: List[str] = Field(description="List of any issues encountered during execution")
    issues_resolved: List[str] = Field(description="List of issues that were successfully resolved")
    recommendations: List[str] = Field(description="Recommendations for future operations or improvements")


class PlanningOutput(BaseModel):
    steps: List[str] = Field(description="List of steps to be performed")
    agents: List[str] = Field(description="List of agents to be used")
    tasks: List[str] = Field(description="List of tasks to be performed")
    expected_output: str = Field(description="Expected output of the planning task")
    ticket_content: str = Field(description="Ticket content")