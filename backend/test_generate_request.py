#!/usr/bin/env python3
"""test_generate.py"""
import requests
import json
import time

url = "http://localhost:8765/generate"

script = """[男] 大家好，歡迎收聽今天的 Podcast。
[女] 我係阿紅，今日我哋傾下行山嘅話題。
[男] 沒錯！我最近去咗大帽山，行咗四個鐘。
[女] 哇，大帽山呀！風景好唔好？
[男] 好好！山頂可以睇到成個香港。
[女] 聽落都好正，下次我一齊去。"""

payload = {
    "script": script,
    "language": "mandarin",
    "speed": 1.0,
}

print("Sending generate request...")
print(f"Script has {len(script)} chars, {script.count(chr(10))+1} lines")
t0 = time.time()
r = requests.post(url, json=payload, timeout=300)
t1 = time.time()
print(f"\nResponse ({t1-t0:.1f}s): {r.status_code}")
print(json.dumps(r.json(), indent=2, ensure_ascii=False))
