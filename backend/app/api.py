from fastapi import FastAPI
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import main

app = FastAPI(
    title="Database Monitoring API",
    description="FastAPI wrapper for CrewAI Database Monitoring Flow"
)

@app.post("/start-monitoring")
def start_monitoring():
    """Start the database monitoring flow"""
    result = main()
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)