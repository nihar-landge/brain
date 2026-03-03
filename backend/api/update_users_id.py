import glob, re
import os

files = glob.glob("/Users/niharlandge/20-Projects/20-25-brain/backend/api/*.py")
changed = 0

for file_path in files:
    with open(file_path, "r") as f:
        content = f.read()
    
    # Replace "user_id == user.id" with "user_id == user.id"
    new_content = content.replace("user_id == user.id", "user_id == user.id")
    
    # Specific adjustment for dopamine_item assignment if any
    new_content = new_content.replace("user_id=user.id", "user_id=user.id")
    
    if content != new_content:
        with open(file_path, "w") as f:
            f.write(new_content)
        changed += 1
        print(f"Updated {file_path}")

print(f"Total files updated: {changed}")
