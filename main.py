import os
import hashlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from database import db, create_document, get_documents

app = FastAPI(title="Abdullah Housing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Auth Schemas ---------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None

# --------- Content Schemas ---------
class ProjectIn(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = Field("upcoming", description="upcoming | ongoing | completed")
    cover_image: Optional[str] = None

class PlotIn(BaseModel):
    plot_no: str
    size: str
    sector: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    status: str = Field("available", description="available | booked | sold")

# --------- Helpers ---------

def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# --------- Root & Test ---------
@app.get("/")
def read_root():
    return {"message": "Abdullah Housing Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# --------- Auth Routes ---------
@app.post("/api/auth/register", response_model=AuthResponse)
def register_user(payload: RegisterRequest):
    existing = db["user"].find_one({"email": payload.email}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_doc = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": sha256_hash(payload.password),
        "is_active": True,
    }
    user_id = create_document("user", user_doc)
    token = sha256_hash(payload.email + "|" + user_id)
    user_public = {"_id": user_id, "name": payload.name, "email": payload.email}
    return AuthResponse(message="Registered successfully", token=token, user=user_public)

@app.post("/api/auth/login", response_model=AuthResponse)
def login_user(payload: LoginRequest):
    user = db["user"].find_one({"email": payload.email}) if db else None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.get("password_hash") != sha256_hash(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = sha256_hash(payload.email + "|" + str(user.get("_id")))
    user_public = {"_id": str(user.get("_id")), "name": user.get("name"), "email": user.get("email")}
    return AuthResponse(message="Login successful", token=token, user=user_public)

# --------- Content Routes ---------
@app.get("/api/projects")
def list_projects(limit: int = 20):
    docs = get_documents("project", {}, limit)
    # Convert ObjectId to string if present
    def norm(d: Any):
        d = dict(d)
        if d.get("_id"):
            d["_id"] = str(d["_id"])
        return d
    return [norm(d) for d in docs]

@app.post("/api/projects")
def create_project(item: ProjectIn):
    doc_id = create_document("project", item.model_dump())
    return {"_id": doc_id, "message": "Project created"}

@app.get("/api/plots")
def list_plots(limit: int = 50, status: Optional[str] = None):
    filt = {"status": status} if status else {}
    docs = get_documents("plot", filt, limit)
    def norm(d: Any):
        d = dict(d)
        if d.get("_id"):
            d["_id"] = str(d["_id"])
        return d
    return [norm(d) for d in docs]

@app.post("/api/plots")
def create_plot(item: PlotIn):
    doc_id = create_document("plot", item.model_dump())
    return {"_id": doc_id, "message": "Plot created"}

@app.get("/api/noc")
def get_noc_info():
    return {
        "title": "NOC & Licenses",
        "overview": "Official No Objection Certificates and licensing details for Abdullah Housing.",
        "documents": [
            {"name": "Town Planning Approval", "status": "Approved", "ref": "TP-2024-0192"},
            {"name": "Environmental Clearance", "status": "Approved", "ref": "ENV-2024-0045"},
            {"name": "Water & Sewerage NOC", "status": "In Progress", "ref": "WS-2025-0109"}
        ]
    }

@app.get("/api/map")
def get_map_info():
    return {
        "title": "Abdullah Housing Master Plan",
        "map_image": "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?q=80&w=1400&auto=format&fit=crop",
        "description": "Zoomable high-level map of the entire society with sectors, roads and amenities."
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
