#!/usr/bin/env python3
"""
Startup script for the Database Monitoring API
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )