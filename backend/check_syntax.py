#!/usr/bin/env python3
import ast
for f in ["qwen3_tts_engine.py", "main.py", "script_parser.py", "audio_merger.py"]:
    try:
        ast.parse(open(f).read())
        print(f"{f} ✅")
    except SyntaxError as e:
        print(f"{f} ❌ {e}")
