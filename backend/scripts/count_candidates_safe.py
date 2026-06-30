import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "talentmind.db")
if not os.path.exists(db_path):
    print("Database not found.")
else:
    try:
        # Open in read-only mode with timeout
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=60.0)
        cursor = conn.execute("SELECT count(*) FROM candidate")
        count = cursor.fetchone()[0]
        print(f"SAFE_CANDIDATES_COUNT: {count}")
        conn.close()
    except Exception as e:
        print(f"Error checking count safely: {e}")
