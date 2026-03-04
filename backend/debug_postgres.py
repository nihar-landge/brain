
import os
import sys
from sqlalchemy import create_engine, text

try:
    # Try connecting to the Postgres DB as defined in docker-compose
    POSTGRES_URL = "postgresql://brain:password@localhost:5432/brain"
    print(f"DEBUG: Trying to connect to Postgres at '{POSTGRES_URL}'")
    
    engine = create_engine(POSTGRES_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"DEBUG: Postgres connection successful! Result: {result.fetchone()}")
        
except Exception as e:
    print(f"DEBUG: Postgres connection FAILED!")
    print(f"DEBUG: Error: {str(e)}")
