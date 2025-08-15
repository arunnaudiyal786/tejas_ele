from crewai.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict
import psycopg2
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from utils.helper import DatabaseConnection


class QueryExecutorTool(BaseTool):
    name: str = "query_executor"
    description: str = "Execute SQL queries on the database and return results"
    
    class ArgsSchema(BaseModel):
        query: str = Field(description="SQL query to execute")
        params: Optional[tuple] = Field(None, description="Parameters for the SQL query")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    args_schema: type = ArgsSchema
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Execute a SQL query and return results"""
        try:
            # Extract parameters from kwargs
            query = kwargs.get('query')
            params = kwargs.get('params')
            
            if not query:
                return {"status": "error", "message": "Query parameter is required"}
            
            db = DatabaseConnection()
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params or ())
                    
                    if query.strip().upper().startswith('SELECT'):
                        # Fetch column names
                        columns = [desc[0] for desc in cur.description]
                        # Fetch all rows
                        rows = cur.fetchall()
                        # Convert to list of dictionaries
                        data = [dict(zip(columns, row)) for row in rows]
                        return {
                            "status": "success",
                            "data": data,
                            "row_count": len(data)
                        }
                    else:
                        # For INSERT, UPDATE, DELETE operations
                        conn.commit()
                        return {
                            "status": "success",
                            "row_count": cur.rowcount,
                            "message": f"Query executed successfully. {cur.rowcount} rows affected."
                        }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

class QueryStatusTool(BaseTool):
    name: str = "query_status_checker"
    description: str = "Check the status of a running database query using process ID or query text"
    
    class ArgsSchema(BaseModel):
        pid: Optional[int] = Field(None, description="Process ID of the query to check")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    args_schema: type = ArgsSchema
    
    def _run(self, **kwargs) -> str:
        try:
            # Extract parameters from kwargs
            pid = kwargs.get('pid')
                        
            db = DatabaseConnection()
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    if pid:
                        cur.execute("""
                            SELECT pid, state, query, query_start 
                            FROM pg_stat_activity 
                            WHERE pid = %s
                        """, (pid,))
                   
                    else:
                        # If no parameters provided, show all active queries
                        cur.execute("""
                            SELECT pid, state, query, query_start 
                            FROM pg_stat_activity 
                            WHERE state = 'active'
                        """)
                    
                    result = cur.fetchone()
                    if result:
                        return f"Query Status - PID: {result[0]}, State: {result[1]}, Started: {result[3]}"
                    return "No active query found"
        except Exception as e:
            return f"Error checking query status: {str(e)}"

class QueryKillerTool(BaseTool):
    name: str = "query_killer"
    description: str = "Kill a running database query using its process ID"
    
    class ArgsSchema(BaseModel):
        pid: Optional[int] = Field(None, description="Process ID of the query to kill")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    args_schema: type = ArgsSchema
    
    def _run(self, **kwargs) -> str:
        pid = kwargs.get('pid')
        if not pid:
            return "Error: Process ID (pid) is required to kill a query"
        
        try:
            db = DatabaseConnection()
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_terminate_backend(%s)", (pid,))
                    result = cur.fetchone()
                    return f"Query termination result: {result[0]}" if result else "Query terminated"
        except Exception as e:
            return f"Error killing query: {str(e)}"

class ConnectionInfoTool(BaseTool):
    name: str = "connection_info_getter"
    description: str = "Get database connection information and active connections"
    
    class ArgsSchema(BaseModel):
        pass  # No parameters needed
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    args_schema: type = ArgsSchema
    
    def _run(self) -> str:
        try:
            db = DatabaseConnection()
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) as active_connections,
                               MAX(backend_start) as latest_connection
                        FROM pg_stat_activity
                        WHERE state = 'active'
                    """)
                    result = cur.fetchone()
                    return f"Active connections: {result[0]}, Latest: {result[1]}"
        except Exception as e:
            return f"Error getting connection info: {str(e)}"

class WeatherTool(BaseTool):
    name: str = "weather_checker"
    description: str = "Get current weather information (unrelated tool for testing)"
    
    class ArgsSchema(BaseModel):
        city: Optional[str] = Field("New York", description="City to get weather for")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    args_schema: type = ArgsSchema
    
    def _run(self, **kwargs) -> str:
        # Mock weather data for testing tool selection
        city = kwargs.get('city', 'New York')
        return f"Weather in {city}: 72°F, Sunny"


class ProductCodeManagerTool(BaseTool):
    name: str = "product_code_manager"
    description: str = "Search for product codes in the database and insert new Medicare Advantage product codes if they don't exist"
    
    class ArgsSchema(BaseModel):
        product_codes: Optional[List[str]] = Field(None, description="List of product codes to search for and insert")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    args_schema: type = ArgsSchema
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Search for product codes and insert new Medicare Advantage codes if missing"""
        product_codes = kwargs.get('product_codes')
        if not product_codes:
            # Default Medicare Advantage product codes for 2025
            product_codes = [
                'PROD_MED_ADV_2025',
                'PROD_MED_ADV_PLUS_2025', 
                'PROD_MED_ADV_PREM_2025'
            ]
        
        try:
            executor = QueryExecutorTool()
            
            # Step 1: Search for existing product codes
            placeholders = ', '.join(['%s'] * len(product_codes))
            search_query = f"""
                SELECT product_code, product_name, product_type, category, effective_date 
                FROM product_catalog 
                WHERE product_code IN ({placeholders})
            """
            
            search_result = executor._run(query=search_query, params=tuple(product_codes))
            
            if search_result["status"] != "success":
                return search_result
            
            existing_codes = [row["product_code"] for row in search_result["data"]]
            missing_codes = [code for code in product_codes if code not in existing_codes]
            
            # Step 2: Insert missing product codes
            inserted_codes = []
            if missing_codes:
                for code in missing_codes:
                    # Determine product details based on code
                    if 'PLUS' in code:
                        product_name = "Medicare Advantage Plus Plan 2025"
                        copay = 20.00
                        deductible = 1000.00
                        oop_max = 6000.00
                        coinsurance = 15
                    elif 'PREM' in code:
                        product_name = "Medicare Advantage Premium Plan 2025"
                        copay = 15.00
                        deductible = 500.00
                        oop_max = 4000.00
                        coinsurance = 10
                    else:
                        product_name = "Medicare Advantage Standard Plan 2025"
                        copay = 25.00
                        deductible = 1500.00
                        oop_max = 8000.00
                        coinsurance = 20
                    
                    insert_query = """
                        INSERT INTO product_catalog (
                            product_code, product_name, product_type, category, 
                            subcategory, network_type, copay_amount, deductible_amount,
                            out_of_pocket_max, coinsurance_percentage, prescription_coverage,
                            dental_coverage, vision_coverage, mental_health_coverage,
                            effective_date, state_availability, age_restrictions
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """
                    
                    insert_params = (
                        code, product_name, 'Medicare Advantage', 'Medicare', 'Senior',
                        'In-Network Only', copay, deductible, oop_max, coinsurance,
                        True, True, True, True, '2025-01-01', 'All States', '65+'
                    )
                    
                    insert_result = executor._run(query=insert_query, params=insert_params)
                    if insert_result["status"] == "success":
                        inserted_codes.append(code)
            
            return {
                "status": "success",
                "existing_codes": existing_codes,
                "missing_codes": missing_codes,
                "inserted_codes": inserted_codes,
                "summary": f"Found {len(existing_codes)} existing codes, inserted {len(inserted_codes)} new codes"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error managing product codes: {str(e)}"
            }

class ProductCodeValidatorTool(BaseTool):
    name: str = "Product Code Validator"
    description: str = "Validates product codes against the product_catalog table"
    
    class ArgsSchema(BaseModel):
        product_codes: Optional[List[str]] = Field(None, description="List of product codes to validate")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    args_schema: type = ArgsSchema
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Validate a list of product codes"""
        product_codes = kwargs.get('product_codes')
        if not product_codes:
            return {"status": "error", "message": "No product codes provided for validation"}
        
        executor = QueryExecutorTool()
        placeholders = ', '.join(['%s'] * len(product_codes))
        query = f"SELECT product_code FROM product_catalog WHERE product_code IN ({placeholders})"
        
        result = executor._run(query=query, params=tuple(product_codes))
        
        if result["status"] == "success":
            found_codes = [row["product_code"] for row in result["data"]]
            missing_codes = [code for code in product_codes if code not in found_codes]
            
            return {
                "status": "success",
                "valid_codes": found_codes,
                "invalid_codes": missing_codes,
                "all_valid": len(missing_codes) == 0
            }
        return result

class BulkInsertTool(BaseTool):
    name: str = "Bulk Insert Tool"
    description: str = "Performs bulk insert operations across multiple tables"
    
    class ArgsSchema(BaseModel):
        table_name: str = Field(description="Name of the table to insert data into")
        data: List[Dict[str, Any]] = Field(None, description="List of records to insert")
        
        model_config = ConfigDict(extra='allow')  # Allow additional fields
    
    args_schema: type = ArgsSchema
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Execute bulk insert operation"""
        table_name = kwargs.get('table_name')
        data = kwargs.get('data')
        
        if not data:
            return {"status": "error", "message": "No data provided for insertion"}
        
        if not table_name:
            return {"status": "error", "message": "Table name is required"}
        
        executor = QueryExecutorTool()
        
        # Build the INSERT query dynamically
        columns = list(data[0].keys())
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        success_count = 0
        errors = []
        
        for record in data:
            values = tuple(record[col] for col in columns)
            result = executor._run(query=query, params=values)
            
            if result["status"] == "success":
                success_count += 1
            else:
                errors.append({"record": record, "error": result["message"]})
        
        return {
            "status": "success" if success_count > 0 else "error",
            "inserted": success_count,
            "failed": len(errors),
            "errors": errors
        }

class TransactionManagerTool(BaseTool):
    name: str = "Transaction Manager"
    description: str = "Manages database transactions with rollback capability"
    
    def __init__(self):
        super().__init__()
        self.connection = None
        self.cursor = None
        self.transaction_log = []
    
    def begin_transaction(self) -> Dict[str, Any]:
        """Start a new transaction"""
        try:
            self.connection = psycopg2.connect(
                host="localhost",
                port=5432, # Changed from 3306 to 5432 for PostgreSQL
                user="elevance_user",
                password="secure_password",
                database="elevance_healthcare"
            )
            self.connection.start_transaction()
            self.cursor = self.connection.cursor(dictionary=True)
            self.transaction_log = []
            return {"status": "success", "message": "Transaction started"}
        except Exception as e: # Changed from psycopg2.Error to Exception
            return {"status": "error", "message": str(e)}
    
    def execute_in_transaction(self, query: str, params: Optional[tuple] = None, **kwargs) -> Dict[str, Any]:
        """Execute a query within the current transaction"""
        if not self.connection or not self.cursor:
            return {"status": "error", "message": "No active transaction"}
        
        try:
            self.cursor.execute(query, params or ())
            self.transaction_log.append({
                "query": query,
                "params": params,
                "timestamp": datetime.now().isoformat()
            })
            
            if query.strip().upper().startswith('SELECT'):
                result = self.cursor.fetchall()
                return {"status": "success", "data": result}
            else:
                return {"status": "success", "rowcount": self.cursor.rowcount}
        except Exception as e: # Changed from psycopg2.Error to Exception
            return {"status": "error", "message": str(e)}
    
    def commit_transaction(self) -> Dict[str, Any]:
        """Commit the current transaction"""
        if not self.connection:
            return {"status": "error", "message": "No active transaction"}
        
        try:
            self.connection.commit()
            result = {
                "status": "success",
                "message": "Transaction committed successfully",
                "operations": len(self.transaction_log)
            }
            return result
        except Exception as e: # Changed from psycopg2.Error to Exception
            return {"status": "error", "message": str(e)}
        finally:
            self._cleanup()
    
    def rollback_transaction(self) -> Dict[str, Any]:
        """Rollback the current transaction"""
        if not self.connection:
            return {"status": "error", "message": "No active transaction"}
        
        try:
            self.connection.rollback()
            result = {
                "status": "success",
                "message": "Transaction rolled back successfully",
                "operations_rolled_back": len(self.transaction_log)
            }
            return result
        except Exception as e: # Changed from psycopg2.Error to Exception
            return {"status": "error", "message": str(e)}
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up database connections"""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None
        self.transaction_log = []