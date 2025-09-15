# backend/app/evals.py
"""
Simple evaluation harness for prompt engineering.
Runs test cases (in evals/cases.json) vs Grok, collects metrics.
"""
import os, json
from app.grok_client import call_grok, GrokError
from app.prompts import qualification_prompt
from typing import List, Dict
from statistics import mean

EVAL_CASES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "evals", "cases.json")

def load_cases():
    with open(EVAL_CASES_PATH, "r") as f:
        return json.load(f)

def run_evals():
    cases = load_cases()
    results = []
    for c in cases:
        prompt = qualification_prompt(c["lead"], c.get("weights", {}))
        try:
            resp = call_grok(prompt)
            text = resp["text"]
            # parse json
            import re
            m = re.search(r"(\{.*\})", text, re.S)
            parsed = {}
            if m:
                parsed = json.loads(m.group(1))
            # heuristics: check if score within tolerance of expected (if provided)
            expected = c.get("expected_score")
            ok = None
            if expected is not None:
                ok = abs(parsed.get("score", 0) - expected) <= c.get("tol", 15)
            results.append({"case_id": c.get("id"), "ok": ok, "parsed": parsed, "expected": expected})
        except GrokError as e:
            results.append({"case_id": c.get("id"), "ok": False, "error": str(e)})
    # summary
    successes = [r for r in results if r.get("ok")]
    overall = {"total": len(results), "ok": len(successes), "cases": results}
    # write results to file
    out_path = os.getenv("EVAL_OUTPUT", "/tmp/grok_evals.json")
    with open(out_path, "w") as f:
        json.dump(overall, f, indent=2)
    return overall
