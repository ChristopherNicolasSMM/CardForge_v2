#!/usr/bin/env python3
"""
CardForge 2.0 — Gerador de Cards via navegador
================================================
Execute:
    python run.py

Depois abra: http://localhost:5000
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
