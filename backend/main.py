import os
from flow import DatabaseFlow

def main():
    # Set environment variables
    os.environ.update({
        'DB_HOST': 'localhost',
        'DB_PORT': '5433',
        'DB_NAME': 'testdb',
        'DB_USER': 'testuser',
        'DB_PASSWORD': 'testpass'
    })

    # Initialize and run flow
    flow = DatabaseFlow()
    result = flow.kickoff()
    print(f"Flow completed: {result}")

if __name__ == "__main__":
    main()