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
