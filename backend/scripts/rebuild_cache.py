import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.caching import disk_cache

def main():
    print("Clearing disk cache...")
    success = disk_cache.clear()
    if success:
        print("Success: Local disk cache cleared.")
    else:
        print("Error: Failed to clear disk cache.")

if __name__ == "__main__":
    main()
