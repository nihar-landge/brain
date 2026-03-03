import glob
files = glob.glob("/Users/niharlandge/20-Projects/20-25-brain/backend/api/*.py")
count = 0 

for title in files:
    with open(title, "r") as f:
        src = f.read()

        src = src.replace("user_id == user.id", "user_id == user.id")

        with open(title, "w") as out:
            out.write(src)
        
        count += 1
print(count)
