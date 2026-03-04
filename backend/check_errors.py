import sqlite3
import re
with open("backend/logs/brain.log", "r") as f:
    for line in f:
        if "OperationalError" in line:
            print(line.strip())
