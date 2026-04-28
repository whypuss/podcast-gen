#!/usr/bin/env python3
"""test_generate2.py"""
import requests
import json
import time

url = "http://localhost:8765/generate"

script = """[男] 大家好，歡迎收聽今天的 Podcast。
[女] 我係阿紅，今日我哋傾下行山嘅話題。
[男] 沒錯！我最近去咗大帽山，行咗四個鐘。"""

payload = {
    "script": script,
    "language": "mandarin",
    "speed": 1.0,
}

print("Sending generate request...")
t0 = time.time()
r = requests.post(url, json=payload, timeout=300)
t1 = time.time()
print(f"\nResponse ({t1-t0:.1f}s): {r.status_code}")
resp = r.json()
print(json.dumps(resp, indent=2, ensure_ascii=False))

if resp.get("success") and resp.get("output_path"):
    print(f"\n✅ 成功！輸出: {resp['output_path']}")
elif resp.get("error"):
    print(f"\n❌ 失敗: {resp['error']}")
    for seg in resp.get("segments", []):
        print(f"  {seg['speaker']}: {'✅' if seg['success'] else '❌'} {seg.get('text','')[:30]}")
