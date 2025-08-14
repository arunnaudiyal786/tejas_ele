import os
import psycopg2
import json
from typing import Dict, Any, List
from crewai.tools import BaseTool 
from crewai_tools import NL2SQLTool
from pydantic import BaseModel, Field
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnectionTool(BaseTool):
    """Base tool for database connections"""
    
    def get_db_connection(self):
        """Get database connection using environment variables"""
        try:
            connection = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'testdb'),
                user=os.getenv('DB_USER', 'testuser'),
                password=os.getenv('DB_PASSWORD', 'testpass'),
                port=os.getenv('DB_PORT', '5432')
            )
            return connection
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

class MemberInsertionTool(DatabaseConnectionTool):
    name: str = "member_insertion_tool"
    description: str = "Insert new member enrollment records into the database. Only member_id is required; all other fields have intelligent defaults. Expects JSON with member_id, name/first_name/last_name, enrollment_period, product_id, provider_id, etc."
    
    def _run(self, member_data: str) -> str:
        """
        Insert new member enrollment records
        Args:
            member_data: JSON string containing member information for insertion
        Returns:
            String result of the insertion operation
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Parse the JSON string to extract member data
            try:
                member_info = json.loads(member_data)
            except json.JSONDecodeError as e:
                return f"Error parsing JSON data: {e}"
            
            # Extract values from the parsed JSON
            # Handle both direct member_data and nested member_data structures
            if 'member_data' in member_info:
                # If the JSON has a nested structure like {"member_data": "..."}
                try:
                    member_info = json.loads(member_info['member_data'])
                except (json.JSONDecodeError, TypeError):
                    return "Error parsing nested member_data JSON"
            
            # Map the JSON fields to database columns with intelligent defaults
            # Only member_id is truly required, everything else can have defaults
            member_id = member_info.get('member_id')
            if not member_id:
                return "Error: member_id is required and cannot be empty"
            
            # Handle name parsing - split full name into first and last
            full_name = member_info.get('name', '')
            if full_name:
                name_parts = full_name.strip().split()
                if len(name_parts) == 1:
                    first_name = name_parts[0]
                    last_name = 'Unknown'
                elif len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = ' '.join(name_parts[1:])
                else:
                    first_name = 'Unknown'
                    last_name = 'Unknown'
            else:
                first_name = member_info.get('first_name', 'Unknown')
                last_name = member_info.get('last_name', 'Unknown')
            
            # Handle dates with fallbacks
            date_of_birth = member_info.get('date_of_birth')
            if not date_of_birth:
                date_of_birth = member_info.get('dob') or '1900-01-01'
            
            enrollment_date = member_info.get('enrollment_date') or member_info.get('enrollment_period') or '2025-01-01'
            
            # Handle plan and product codes
            plan_code = member_info.get('plan_code') or member_info.get('plan') or 'DEFAULT'
            product_code = member_info.get('product_code') or member_info.get('product_id') or 'PROD_HMO_001'
            
            # Status and provider
            status = member_info.get('status', 'ACTIVE')
            primary_care_provider_id = member_info.get('primary_care_provider_id') or member_info.get('provider_id')
            
            # Coverage dates
            coverage_effective_date = member_info.get('coverage_effective_date') or enrollment_date
            coverage_termination_date = member_info.get('coverage_termination_date')
            
            # Query to insert a new member
            insert_query = """
            INSERT INTO member_enrollment (
                member_id, first_name, last_name, date_of_birth, enrollment_date,
                plan_code, product_code, status, primary_care_provider_id,
                coverage_effective_date, coverage_termination_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING member_id, first_name, last_name;
            """
            
            # Execute the prepared statement with the extracted values
            cursor.execute(insert_query, (
                member_id, first_name, last_name, date_of_birth, enrollment_date,
                plan_code, product_code, status, primary_care_provider_id,
                coverage_effective_date, coverage_termination_date
            ))
            
            if cursor.description:
                results = cursor.fetchall()
                conn.commit()
                return f"Successfully inserted member record: {results}"
            else:
                conn.commit()
                return "Member insertion completed successfully"
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Member insertion failed: {e}")
            return f"Error inserting member records: {e}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

class ProviderInsertionTool(DatabaseConnectionTool):
    name: str = "provider_insertion_tool"
    description: str = "Insert new provider records into the provider network. Only provider_id is required; all other fields have intelligent defaults. Expects JSON with provider_id, name, specialty, product_code, etc."
    
    def _run(self, provider_data: str) -> str:
        """
        Insert new provider records
        Args:
            provider_data: JSON string containing provider information for insertion
        Returns:
            String result of the insertion operation
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Parse the JSON string to extract provider data
            try:
                provider_info = json.loads(provider_data)
            except json.JSONDecodeError as e:
                return f"Error parsing JSON data: {e}"
            
            # Extract values from the parsed JSON with intelligent defaults
            # Only provider_id is truly required
            provider_id = provider_info.get('provider_id')
            if not provider_id:
                return "Error: provider_id is required and cannot be empty"
            
            # Handle provider name with fallbacks
            provider_name = provider_info.get('provider_name') or provider_info.get('name', 'Unknown Provider')
            
            # Handle specialty with fallbacks
            specialty = provider_info.get('specialty') or provider_info.get('specialization', 'General')
            
            # Handle product code with fallbacks
            product_code = provider_info.get('product_code') or provider_info.get('product_id', 'PROD_HMO_001')
            
            # Handle provider type
            provider_type = provider_info.get('provider_type') or provider_info.get('type', 'Primary Care')
            
            # Handle NPI number
            npi_number = provider_info.get('npi_number') or provider_info.get('npi', '0000000000')
            
            # Handle network tier
            network_tier = provider_info.get('network_tier') or provider_info.get('tier', 'Tier 2')
            
            # Handle contact information
            phone_number = provider_info.get('phone_number') or provider_info.get('phone')
            email = provider_info.get('email')
            
            # Handle address information
            address_line1 = provider_info.get('address_line1') or provider_info.get('address')
            city = provider_info.get('city')
            state = provider_info.get('state')
            zip_code = provider_info.get('zip_code') or provider_info.get('zip')
            
            # Handle other fields
            languages_spoken = provider_info.get('languages_spoken') or provider_info.get('languages', 'English')
            accepting_new_patients = provider_info.get('accepting_new_patients', True)
            quality_rating = provider_info.get('quality_rating', 4.0)
            patient_volume = provider_info.get('patient_volume', 1000)
            
            # Query to insert a new provider with comprehensive fields
            insert_query = """
            INSERT INTO provider_network (
                provider_id, npi_number, provider_name, provider_type, specialty, 
                product_code, network_tier, address_line1, city, state, zip_code,
                phone_number, email, languages_spoken, accepting_new_patients,
                quality_rating, patient_volume
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING provider_id, provider_name;
            """
            
            # Execute the prepared statement with the extracted values
            cursor.execute(insert_query, (
                provider_id, npi_number, provider_name, provider_type, specialty,
                product_code, network_tier, address_line1, city, state, zip_code,
                phone_number, email, languages_spoken, accepting_new_patients,
                quality_rating, patient_volume
            ))
            
            if cursor.description:
                results = cursor.fetchall()
                conn.commit()
                return f"Successfully inserted provider record: {results}"
            else:
                conn.commit()
                return "Provider insertion completed successfully"
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Provider insertion failed: {e}")
            return f"Error inserting provider records: {e}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

class DuplicateDetectionTool(DatabaseConnectionTool):
    name: str = "duplicate_detection_tool"
    description: str = "Detect duplicate member records based on personal information"
    
    def _run(self, detection_criteria: str = "default") -> str:
        """
        Detect duplicate member records
        Args:
            detection_criteria: Criteria for detecting duplicates (default uses name and DOB)
        Returns:
            String containing duplicate detection results
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Query to find potential duplicates based on name and date of birth
            duplicate_query = """
            SELECT 
                first_name, last_name, date_of_birth,
                COUNT(*) as duplicate_count,
                STRING_AGG(member_id, ', ') as member_ids,
                STRING_AGG(enrollment_date::text, ', ') as enrollment_dates
            FROM member_enrollment 
            GROUP BY first_name, last_name, date_of_birth
            HAVING COUNT(*) > 1
            ORDER BY first_name, last_name;
            """
            
            cursor.execute(duplicate_query)
            duplicates = cursor.fetchall()
            
            if duplicates:
                result = "Duplicate members found:\n"
                for dup in duplicates:
                    result += f"Name: {dup[0]} {dup[1]}, DOB: {dup[2]}, Count: {dup[3]}\n"
                    result += f"Member IDs: {dup[4]}\n"
                    result += f"Enrollment Dates: {dup[5]}\n---\n"
                return result
            else:
                return "No duplicate member records found"
                
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            return f"Error detecting duplicates: {e}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

class DuplicateCleanupTool(DatabaseConnectionTool):
    name: str = "duplicate_cleanup_tool"
    description: str = "Remove duplicate member records while preserving the earliest enrollment"
    
    def _run(self, cleanup_query: str) -> str:
        """
        Clean up duplicate member records
        Args:
            cleanup_query: SQL query for removing duplicate records
        Returns:
            String result of the cleanup operation
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Execute the cleanup query provided by the agent
            cursor.execute(cleanup_query)
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return f"Successfully removed {deleted_count} duplicate member records"
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Duplicate cleanup failed: {e}")
            return f"Error cleaning up duplicates: {e}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

class DataValidationTool(DatabaseConnectionTool):
    name: str = "data_validation_tool"
    description: str = "Validate data integrity and referential constraints"
    
    def _run(self, validation_type: str = "full") -> str:
        """
        Perform data validation checks
        Args:
            validation_type: Type of validation to perform (full, members, providers, etc.)
        Returns:
            String containing validation results
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            validation_results = []
            
            # Check member enrollment integrity
            cursor.execute("""
                SELECT COUNT(*) FROM member_enrollment me 
                LEFT JOIN product_catalog pc ON me.product_code = pc.product_code 
                WHERE pc.product_code IS NULL;
            """)
            invalid_products = cursor.fetchone()[0]
            validation_results.append(f"Members with invalid product codes: {invalid_products}")
            
            # Check provider network integrity
            cursor.execute("""
                SELECT COUNT(*) FROM provider_network pn 
                LEFT JOIN product_catalog pc ON pn.product_code = pc.product_code 
                WHERE pc.product_code IS NULL;
            """)
            invalid_provider_products = cursor.fetchone()[0]
            validation_results.append(f"Providers with invalid product codes: {invalid_provider_products}")
            
            # Check for remaining duplicates
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT first_name, last_name, date_of_birth
                    FROM member_enrollment 
                    GROUP BY first_name, last_name, date_of_birth
                    HAVING COUNT(*) > 1
                ) duplicates;
            """)
            remaining_duplicates = cursor.fetchone()[0]
            validation_results.append(f"Remaining duplicate member groups: {remaining_duplicates}")
            
            # Check total record counts
            cursor.execute("SELECT COUNT(*) FROM member_enrollment;")
            total_members = cursor.fetchone()[0]
            validation_results.append(f"Total member records: {total_members}")
            
            cursor.execute("SELECT COUNT(*) FROM provider_network;")
            total_providers = cursor.fetchone()[0]
            validation_results.append(f"Total provider records: {total_providers}")
            
            return "Data Validation Results:\n" + "\n".join(validation_results)
                
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return f"Error during data validation: {e}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


class FlexibleDataInsertionTool(DatabaseConnectionTool):
    name: str = "flexible_data_insertion_tool"
    description: str = "Flexibly insert data into any table with automatic field mapping and default values. Expects JSON with table_name and data fields."
    
    def _run(self, insertion_data: str) -> str:
        """
        Flexibly insert data into any table with automatic field mapping
        Args:
            insertion_data: JSON string containing table_name and data fields
        Returns:
            String result of the insertion operation
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Parse the JSON string
            try:
                data_info = json.loads(insertion_data)
            except json.JSONDecodeError as e:
                return f"Error parsing JSON data: {e}"
            
            # Extract table name and data
            table_name = data_info.get('table_name')
            if not table_name:
                return "Error: table_name is required in the JSON data"
            
            data_fields = data_info.get('data', {})
            if not data_fields:
                return "Error: data object is required in the JSON data"
            
            # Get table schema to understand available columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns_info = cursor.fetchall()
            if not columns_info:
                return f"Error: Table '{table_name}' not found or no access"
            
            # Build dynamic INSERT query
            available_columns = []
            values = []
            placeholders = []
            
            for col_name, data_type, is_nullable, default_value in columns_info:
                # Skip auto-generated columns
                if col_name in ['created_at', 'updated_at']:
                    continue
                
                # Get value from data or use default
                value = data_fields.get(col_name)
                
                # Handle different data types and defaults
                if value is None:
                    if default_value is not None:
                        # Use database default
                        continue
                    elif is_nullable == 'YES':
                        # Allow NULL
                        values.append(None)
                        available_columns.append(col_name)
                        placeholders.append('NULL')
                    else:
                        # Use sensible defaults based on data type
                        if 'date' in data_type.lower():
                            values.append('1900-01-01')
                        elif 'varchar' in data_type.lower() or 'text' in data_type.lower():
                            values.append('Unknown')
                        elif 'int' in data_type.lower() or 'decimal' in data_type.lower():
                            values.append(0)
                        elif 'boolean' in data_type.lower():
                            values.append(False)
                        else:
                            values.append('Unknown')
                        
                        available_columns.append(col_name)
                        placeholders.append('%s')
                else:
                    values.append(value)
                    available_columns.append(col_name)
                    placeholders.append('%s')
            
            if not available_columns:
                return f"Error: No valid columns found for table '{table_name}'"
            
            # Build and execute the INSERT query
            insert_query = f"""
            INSERT INTO {table_name} ({', '.join(available_columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *;
            """
            
            # Execute the query
            cursor.execute(insert_query, values)
            
            if cursor.description:
                results = cursor.fetchall()
                conn.commit()
                return f"Successfully inserted data into {table_name}: {results}"
            else:
                conn.commit()
                return f"Successfully inserted data into {table_name}"
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Flexible data insertion failed: {e}")
            return f"Error during flexible data insertion: {e}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()