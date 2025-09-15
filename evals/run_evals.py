# evals/run_evals.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.evals import run_evals
import json

if __name__ == "__main__":
    out = run_evals()
    print("Evals summary:", json.dumps(out, indent=2))
    print("Detailed results written to /tmp/grok_evals.json (or EVAL_OUTPUT env var)")
