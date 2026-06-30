import sys
import os
import shutil
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config.config import settings

def main():
    parser = argparse.ArgumentParser(description="Load dataset to uploads folder.")
    parser.add_argument("--file", required=True, help="Path to raw dataset file.")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File does not exist: {args.file}")
        sys.exit(1)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = os.path.basename(args.file)
    dest = os.path.join(settings.UPLOAD_DIR, filename)

    try:
        shutil.copy2(args.file, dest)
        print(f"Success: File loaded to upload directory: {dest}")
    except Exception as e:
        print(f"Error copying file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
