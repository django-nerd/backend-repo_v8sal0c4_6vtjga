from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from database import create_document, get_documents, db
import importlib

# Pydantic request model for lead creation
class LeadIn(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = "landing"

class LeadOut(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None

app = FastAPI(title="Vaelin API", version="1.0.0")

# CORS: allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
async def test():
    return {
        "status": "ok",
        "database_connected": db is not None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/schema")
async def get_schema():
    """Expose schemas for the database viewer (if used)."""
    try:
        schemas_module = importlib.import_module("schemas")
        # Collect model annotations if available
        doc = getattr(schemas_module, "__doc__", "") or ""
        return {"module_doc": doc}
    except Exception:
        return {"module_doc": ""}

@app.post("/leads", response_model=dict)
async def create_lead(lead: LeadIn):
    try:
        lead_dict = lead.model_dump()
        lead_id = create_document("lead", lead_dict)
        return {"id": lead_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leads", response_model=List[LeadOut])
async def list_leads(limit: int = 25):
    try:
        docs = get_documents("lead", limit=limit)
        # Normalize MongoDB documents
        results = []
        for d in docs:
            results.append({
                "id": str(d.get("_id")),
                "email": d.get("email"),
                "name": d.get("name"),
                "company": d.get("company"),
                "source": d.get("source"),
                "created_at": d.get("created_at"),
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
