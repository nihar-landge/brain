from utils.database import engine, create_tables
from sqlalchemy import inspect
create_tables()
inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tables in SQLite DB:", tables)
