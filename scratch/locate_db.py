import os
import sqlite3

print(f"Current Working Directory: {os.getcwd()}")
db_name = "draft_history.db"
print(f"Absolute path of {db_name}: {os.path.abspath(db_name)}")
if os.path.exists(db_name):
    print(f"File exists. Size: {os.path.getsize(db_name)}")
    print(f"Last modified: {os.path.getmtime(db_name)}")
else:
    print("File does not exist in current directory")

# Search for other draft_history.db files on the system (limited search)
import glob
print("Searching for other instances...")
for f in glob.glob("**/draft_history.db", recursive=True):
    print(f"Found: {os.path.abspath(f)}")
