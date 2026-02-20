import os
import re

backend_dir = "/Users/niharlandge/20-Projects/20-25-brain/backend"

for root, dirs, files in os.walk(backend_dir):
    if "venv" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()

            if "datetime.utcnow" in content:
                # Add timezone to datetime import if not already there
                if "import datetime" in content or "from datetime import" in content:
                    if "timezone" not in content:
                        content = content.replace("from datetime import datetime", "from datetime import datetime, timezone")
                        content = content.replace("from datetime import datetime,", "from datetime import datetime, timezone,")
                
                # Replace default=datetime.utcnow with default=lambda: datetime.now(timezone.utc)
                content = content.replace("default=datetime.utcnow", "default=lambda: datetime.now(timezone.utc)")
                
                # Replace datetime.utcnow() with datetime.now(timezone.utc)
                content = content.replace("datetime.utcnow()", "datetime.now(timezone.utc)")
                
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"Updated {filepath}")
