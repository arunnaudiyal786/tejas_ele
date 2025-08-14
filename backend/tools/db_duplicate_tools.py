
from crewai.tools import BaseTool
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from utils.helper import DatabaseConnection


class DBDuplicateCheckerTicketParserTool(BaseTool):
    name: str = "ticket_parser"
    description: str = "Parse ticket information to extract table names and duplicate criteria"
    
    class ArgsSchema(BaseModel):
        ticket_content: Optional[str] = Field(None, description="Content of the ticket to parse")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    args_schema: type = ArgsSchema
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Parse ticket content to identify tables and duplicate detection criteria"""
        ticket_content = kwargs.get('ticket_content')
        if not ticket_content:
            return {
                "status": "error",
                "message": "No ticket content provided for parsing"
            }
        
        import re
        
        # Extract table names (looking for patterns like 'table_name', "table_name", or table references)
        table_pattern = r'(?:table|from|into|update)\s+([a-zA-Z_][a-zA-Z0-9_]*)|([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)'
        tables = re.findall(table_pattern, ticket_content, re.IGNORECASE)
        table_names = [t[0] or t[1] for t in tables if t[0] or t[1]]
        
        # Extract field names for duplicate checking
        field_pattern = r'(?:field|column)\s+([a-zA-Z_][a-zA-Z0-9_]*)|duplicate\s+on\s+([a-zA-Z_][a-zA-Z0-9_]*)|by\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        fields = re.findall(field_pattern, ticket_content, re.IGNORECASE)
        field_names = [f[0] or f[1] or f[2] for f in fields if f[0] or f[1] or f[2]]
        
        return {
            "tables": list(set(table_names)) if table_names else ["users", "products", "orders"],  # Default tables
            "fields": list(set(field_names)) if field_names else ["email", "name", "id"],  # Default fields
            "ticket_content": ticket_content
        }

class DBDuplicateCheckerDuplicateDetectorTool(BaseTool):
    name: str = "duplicate_detector"
    description: str = "Detect duplicate records in database tables"
    
    class ArgsSchema(BaseModel):
        table_name: Optional[str] = Field(None, description="Name of the table to check for duplicates")
        fields: Optional[List[str]] = Field(None, description="List of fields to check for duplicates")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields

    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()

    def _run(self, **kwargs) -> Dict[str, Any]:
        """Find duplicate records in specified table and fields"""
        table_name = kwargs.get('table_name')
        fields = kwargs.get('fields')
        
        if not table_name or not fields:
            return {
                "status": "error",
                "message": "Both table_name and fields are required for duplicate detection"
            }
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Build query to find duplicates
            fields_str = ', '.join(fields)
            query = f"""
                SELECT {fields_str}, COUNT(*) as duplicate_count
                FROM {table_name}
                GROUP BY {fields_str}
                HAVING COUNT(*) > 1
                ORDER BY duplicate_count DESC
                LIMIT 100
            """
            
            cursor.execute(query)
            duplicates = cursor.fetchall()
            
            # Convert to list of dictionaries
            duplicate_list = []
            for row in duplicates:
                row_dict = {}
                for i, field in enumerate(fields):
                    row_dict[field] = row[i]
                row_dict['duplicate_count'] = row[-1]  # Last column is count
                duplicate_list.append(row_dict)
            
            total_duplicate_groups = len(duplicate_list)
            total_duplicate_records = sum(d["duplicate_count"] for d in duplicate_list)
            
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "table": table_name,
                "fields": fields,
                "duplicate_groups": total_duplicate_groups,
                "total_duplicates": total_duplicate_records,
                "details": duplicate_list[:10]  # Top 10 duplicate groups
            }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error detecting duplicates in {table_name}: {str(e)}"
            }

class DBDuplicateQueryExecutor(BaseTool):
    name: str = "duplicate_query_executor"
    description: str = "Execute queries to delete duplicate records based on specific criteria"
    
    class ArgsSchema(BaseModel):
        table_name: Optional[str] = Field(None, description="Name of the table to delete duplicates from")
        fields: Optional[List[str]] = Field(None, description="List of fields to identify duplicates")
        record_to_keep: Optional[Dict[str, Any]] = Field(None, description="Record to keep (will not be deleted)")
        record_to_delete: Optional[Dict[str, Any]] = Field(None, description="Record to delete")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields

    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Delete duplicate records based on specific field criteria and record details"""
        table_name = kwargs.get('table_name')
        fields = kwargs.get('fields')
        record_to_keep = kwargs.get('record_to_keep')
        record_to_delete = kwargs.get('record_to_delete')
        
        if not table_name or not fields or not record_to_keep or not record_to_delete:
            return {
                "status": "error",
                "message": "All parameters (table_name, fields, record_to_keep, record_to_delete) are required"
            }
        
        try:
            from psycopg2.extras import RealDictCursor

            conn = self.db.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build WHERE clause for the record to delete
            where_conditions = []
            for field in fields:
                if field in record_to_delete:
                    where_conditions.append(f"{field} = %s")
            
            if not where_conditions:
                cursor.close()
                conn.close()
                return {
                    "status": "error",
                    "message": "No valid fields provided for deletion criteria"
                }
            
            where_clause = " AND ".join(where_conditions)
            
            # First, verify the record exists and get its ID
            select_query = f"""
                SELECT * FROM {table_name}
                WHERE {where_clause}
                LIMIT 1
            """
            
            # Execute select query with parameters
            select_values = [record_to_delete[field] for field in fields if field in record_to_delete]
            cursor.execute(select_query, select_values)
            select_result = cursor.fetchall()
            
            if not select_result:
                cursor.close()
                conn.close()
                return {
                    "status": "error",
                    "message": f"Record not found in {table_name} with the specified criteria"
                }
            
            # Build DELETE query
            delete_query = f"""
                DELETE FROM {table_name}
                WHERE {where_clause}
            """
            
            # Execute delete query with parameters
            cursor.execute(delete_query, select_values)
            affected_rows = cursor.rowcount
            
            # Commit the transaction
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "message": f"Successfully deleted duplicate record from {table_name}",
                "table": table_name,
                "deleted_criteria": where_clause,
                "affected_rows": affected_rows
            }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing duplicate deletion query: {str(e)}"
            }
    
    def delete_duplicates_by_criteria(self, table_name: str, fields: List[str], duplicate_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Delete all duplicate records that match specific criteria"""
        try:
            from psycopg2.extras import RealDictCursor

            conn = self.db.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build WHERE clause for duplicate criteria
            where_conditions = []
            for field in fields:
                if field in duplicate_criteria:
                    where_conditions.append(f"{field} = %s")
            
            if not where_conditions:
                cursor.close()
                conn.close()
                return {
                    "status": "error",
                    "message": "No valid fields provided for deletion criteria"
                }
            
            where_clause = " AND ".join(where_conditions)
            
            # Count records before deletion
            count_query = f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE {where_clause}
            """
            
            # Execute count query with parameters
            count_values = [duplicate_criteria[field] for field in fields if field in duplicate_criteria]
            cursor.execute(count_query, count_values)
            count_result = cursor.fetchone()
            
            record_count = count_result['count'] if count_result else 0
            
            if record_count <= 1:
                cursor.close()
                conn.close()
                return {
                    "status": "info",
                    "message": f"No duplicate records found in {table_name} with the specified criteria",
                    "table": table_name,
                    "criteria": where_clause
                }
            
            # Delete all but one record (keep the first one)
            delete_query = f"""
                DELETE FROM {table_name}
                WHERE {where_clause}
                AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM {table_name}
                        WHERE {where_clause}
                        LIMIT 1
                    ) AS keep_record
                )
            """
            
            # Execute delete query with parameters
            cursor.execute(delete_query, count_values)
            deleted_count = cursor.rowcount
            
            # Commit the transaction
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "message": f"Successfully deleted {deleted_count} duplicate records from {table_name}",
                "table": table_name,
                "deleted_criteria": where_clause,
                "records_deleted": deleted_count,
                "records_kept": 1
            }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing bulk duplicate deletion: {str(e)}"
            }