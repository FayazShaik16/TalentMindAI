import sys
import os
import argparse

# Inject root folder into search path to support relative app imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pipeline import pipeline

def main():
    parser = argparse.ArgumentParser(description="Audit dataset schema columns.")
    parser.add_argument("--file", required=True, help="Path to raw dataset file.")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File does not exist: {args.file}")
        sys.exit(1)

    try:
        records = pipeline.parse_file(args.file)
        if not records:
            print("Error: Empty dataset.")
            sys.exit(1)

        report = pipeline.detect_schema(records[0])
        print("\n=== Dataset Schema Audit Report ===")
        print(f"File: {args.file}")
        print(f"Total Rows Found: {len(records)}")
        print(f"Columns Found: {', '.join(report['columns_found'])}")

        if report["is_valid"]:
            print("Result: [VALID] All expected columns are present.")
        else:
            print(f"Result: [INVALID] Missing required columns: {', '.join(report['missing_required_columns'])}")
    except Exception as e:
        print(f"Error parsing file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
