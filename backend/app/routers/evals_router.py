# backend/app/routers/evals_router.py
from fastapi import APIRouter
from app.evals import run_evals
router = APIRouter(prefix="/evals", tags=["evals"])

@router.get("/run")
def run():
    results = run_evals()
    return {"results_summary": results}
