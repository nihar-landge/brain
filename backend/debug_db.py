
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the current directory to sys.path to import config
sys.path.append(os.getcwd())

try:
    from config import DATABASE_URL
    print(f"DEBUG: DATABASE_URL is '{DATABASE_URL}'")
    
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"DEBUG: Database connection successful! Result: {result.fetchone()}")
        
except Exception as e:
    print(f"DEBUG: Database connection FAILED!")
    print(f"DEBUG: Error: {str(e)}")
    import traceback
    traceback.print_exc()
