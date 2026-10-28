# backend/ is owned by Member A
- Python 3.11, FastAPI. Run: uvicorn app.main:app --reload --port 8000
- Tests: pytest -q
- Follow contracts/api.md, contracts/scoring.md, contracts/events.md exactly.
- Heavy models load once at startup (app/models.py), never per request.
