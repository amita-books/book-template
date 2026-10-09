#!/usr/bin/env python3
"""[로컬 전용] 예제 파일의 80칸 초과 줄을 찾는다 (한글은 2칸).
   python3 scripts/check-width.py ch01-history board"""
import sys, unicodedata
from pathlib import Path

EXT = {".java", ".jsp", ".xml", ".sql", ".properties", ".html", ".css",
       ".js", ".sh"}
bad = 0
for root in sys.argv[1:] or ["."]:
    for f in sorted(Path(root).rglob("*")):
        if f.suffix not in EXT or "target" in f.parts:
            continue
        if f.name.endswith(".min.js"):   # 내려받은 라이브러리(jQuery 등)
            continue
        for no, line in enumerate(f.read_text("utf-8").splitlines(), 1):
            w = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1
                    for c in line.expandtabs(4))
            if w > 80:
                bad += 1
                print("%s:%d  %d칸" % (f, no, w))
print("80칸 초과: %d줄" % bad)
sys.exit(1 if bad else 0)
