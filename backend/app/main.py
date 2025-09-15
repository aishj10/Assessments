# backend/app/main.py
import uvicorn
from fastapi import FastAPI
from app.database import init_db
from app.routers import leads, evals_router
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="SDR Grok Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router)
app.include_router(evals_router.router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
