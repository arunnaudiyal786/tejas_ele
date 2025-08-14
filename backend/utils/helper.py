import os
import json
from langchain_openai import ChatOpenAI
import psycopg2

def load_initial_files():
    """Load ticket content from initial_files folder"""
    try:
        # Get the directory where this script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to reach the backend directory
        backend_dir = os.path.dirname(current_dir)
        
        # Load ticket description
        ticket_file_path = os.path.join(backend_dir, 'initial_files', 'ticket_description.txt')
        if not os.path.exists(ticket_file_path):
            raise FileNotFoundError(f"Ticket file not found at: {ticket_file_path}")
            
        with open(ticket_file_path, 'r', encoding='utf-8') as f:
            ticket_content = f.read().strip()
        
        # Validate that we have content
        if not ticket_content:
            raise ValueError("Ticket content is empty")
        
        print(f"✅ Loaded ticket content: {len(ticket_content)} characters")
        
        return ticket_content
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
        raise
    except Exception as e:
        print(f"❌ Error loading initial files: {e}")
        raise

def reload_initial_files():
    """Reload the initial files and return the content"""
    print("🔄 Reloading initial files...")
    return load_initial_files()

def get_llm_config():
    """Get LLM configuration using environment variables"""
    try:
        # Create ChatOpenAI instance using environment variables
        llm = ChatOpenAI(
            model=os.getenv('LLM_MODEL', 'gpt-4o'),
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
        
        return llm
        
    except Exception as e:
        print(f"❌ Error loading LLM configuration: {e}")
        raise


class DatabaseConnection:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5433)),
            'database': os.getenv('DB_NAME', 'testdb'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
    
    def get_connection(self):
        return psycopg2.connect(**self.conn_params)