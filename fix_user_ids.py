import os

api_dir = "/Users/niharlandge/20-Projects/20-25-brain/backend/api"
files = [
    "journal.py", "chat.py", "calendar.py", "social_graph.py", 
    "dopamine.py", "goals.py", "context_switching.py", 
    "habits.py", "predictions.py", "tasks.py"
]

for filename in files:
    filepath = os.path.join(api_dir, filename)
    with open(filepath, 'r') as f:
        content = f.read()

    has_changes = False
    
    # Add imports
    if ("user_id=1" in content or "user_id = 1" in content) and "verify_api_key" not in content:
        content = content.replace("from utils.database import get_db", "from utils.database import get_db\nfrom models.user import User\nfrom utils.auth import verify_api_key")
        has_changes = True

    if "user_id=1" in content or "user_id = 1" in content:
        # Most of them have db: Session = Depends(get_db)
        content = content.replace("db: Session = Depends(get_db)", "user: User = Depends(verify_api_key), db: Session = Depends(get_db)")
        content = content.replace("user_id=1", "user_id=user.id")
        content = content.replace("user_id = 1", "user_id = user.id")
        has_changes = True

    if has_changes:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filename}")

