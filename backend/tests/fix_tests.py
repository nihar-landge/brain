import os
import glob
import re

TEST_DIR = "/Users/niharlandge/20-Projects/20-25-brain/backend/tests"
files = glob.glob(os.path.join(TEST_DIR, "test_*.py"))

for file_path in files:
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    new_lines = []
    for line in lines:
        # 1. Clean up test signatures
        if line.strip().startswith("def test_"):
            # Strip previous attempts if any
            line = re.sub(r'\(self.*?client.*?\):', '(self, client):', line)
            # Add back properly
            line = line.replace('(self, client):', '(self, client, auth_headers):')
            
        # 2. Add auth_headers to client calls correctly
        if "client." in line and not "headers=auth_headers" in line:
            # Match any client.(get|post|put|delete)("string_url"
            line = re.sub(r'(client\.(?:get|post|put|delete)\([^,)]+)', r'\1, headers=auth_headers', line)
            
        new_lines.append(line)
        
    with open(file_path, 'w') as f:
        f.writelines(new_lines)

print("Fixed keyword arguments in test client calls safely.")
