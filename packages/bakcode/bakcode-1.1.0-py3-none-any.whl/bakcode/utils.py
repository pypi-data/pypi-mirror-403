# -*- coding: utf-8 -*-
"""Utility functions for bakcode"""

import os, sys

def info(msg):
    print(f"[bakcode] {msg}")

def die(msg, code=1):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(code)

def safe_remove(path):
    try:
        os.remove(path)
        info(f"삭제: {path}")
    except OSError:
        pass

def parse_size(s):
    s = s.strip()
    if not s:
        die("size is empty")
    if s[-1].isdigit():
        n = int(s)
        if n <= 0:
            die("size must be > 0")
        return n
    unit = s[-1].upper()
    num = float(s[:-1])
    if num <= 0:
        die("size must be > 0")
    if unit == 'K': mul = 1024
    elif unit == 'M': mul = 1024**2
    elif unit == 'G': mul = 1024**3
    else: die(f"unknown unit: {unit}")
    return int(num * mul)
