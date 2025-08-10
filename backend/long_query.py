import os
import psycopg2

def run_long_query():
    """Run a long running query to test monitoring"""
    conn_params = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                # Create test table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS long_running_table (
                        id SERIAL PRIMARY KEY,
                        data TEXT
                    );
                """)
                
                # Insert test data if table is empty
                cur.execute("SELECT COUNT(*) FROM long_running_table")
                if cur.fetchone()[0] == 0:
                    cur.execute("""
                        INSERT INTO long_running_table (data) 
                        SELECT 'test_data_' || generate_series(1, 1000)
                    """)
                
                conn.commit()
                print("Starting long running query...")
                
                # Run the long query
                cur.execute("SELECT pg_sleep(300), COUNT(*) FROM long_running_table WHERE data LIKE '%5%'")
                result = cur.fetchone()
                print(f"Long query completed: {result}")
                
    except Exception as e:
        print(f"Error running long query: {e}")

if __name__ == "__main__":
    # Set environment variables for standalone execution
    os.environ.update({
        'DB_HOST': 'localhost',
        'DB_PORT': '5433',
        'DB_NAME': 'testdb',
        'DB_USER': 'testuser',
        'DB_PASSWORD': 'testpass'
    })
    
    run_long_query()
