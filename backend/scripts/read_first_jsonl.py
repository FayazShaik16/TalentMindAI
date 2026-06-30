import json

file_path = "c:/Users/user/Desktop/TalentMindAI_IndiaRuns/backend/uploads/candidates.jsonl"
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            record = json.loads(line)
            print("KEYS:", list(record.keys()))
            print("FIRST RECORD:", json.dumps(record, indent=2)[:500])
            break
