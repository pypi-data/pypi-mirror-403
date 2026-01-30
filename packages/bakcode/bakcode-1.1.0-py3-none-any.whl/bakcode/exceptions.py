# -*- coding: utf-8 -*-
"""Custom exceptions for bakcode"""

import sys


class bakcodeError(Exception):
    """Base exception for all bakcode errors"""
    pass


def die(msg, code=1):
    """Print error and exit"""
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(code)
