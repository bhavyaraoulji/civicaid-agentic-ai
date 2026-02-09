import json
import requests
import time

URL = "http://127.0.0.1:8000/eval"
DATASET = "eval_dataset.jsonl"

with open(DATASET, "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        r = requests.post(URL, json=row, timeout=60)
        print(r.status_code, row["expected_domain"], "->", r.json().get("state", {}).get("domain"))
        time.sleep(1)

print("DONE")
