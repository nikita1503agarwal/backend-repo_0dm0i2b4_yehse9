import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="Arivar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        # Try to import database module
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ----- Lead capture endpoints -----
try:
    from schemas import Lead  # type: ignore
    from database import create_document  # type: ignore
except Exception:
    Lead = None  # type: ignore
    create_document = None  # type: ignore


@app.post("/api/leads")
def create_lead(lead: Any):
    """Create a lead from website forms (contact sales or request demo)."""
    if Lead is None or create_document is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Validate using Lead schema
    try:
        lead_model = Lead(**lead)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        lead_id = create_document("lead", lead_model)
        return {"status": "ok", "id": lead_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Optional: expose available schemas for tooling
@app.get("/schema")
def get_schema() -> Dict[str, Dict[str, Any]]:
    try:
        import schemas as schemas_module  # type: ignore
        result: Dict[str, Dict[str, Any]] = {}
        for name in dir(schemas_module):
            obj = getattr(schemas_module, name)
            if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
                result[name] = obj.model_json_schema()  # type: ignore
        return result
    except Exception:
        return {}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
