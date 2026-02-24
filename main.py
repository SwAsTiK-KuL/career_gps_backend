from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from career_gps.model import CareerPathModel
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

load_dotenv()

app = FastAPI(
    title="Career GPS API",
    description="AI Career Path Generator - Mumbai Edition",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MongoDB setup ──────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["career_gps"]
collection = db["roadmap_logs"]

# ── Request model ──────────────────────────────────────────────
class RoadmapRequest(BaseModel):
    skills: list[str]
    designation: str = ""
    job_description: str
    model: str = "gemini-2.5-flash"

# ── Routes ─────────────────────────────────────────────────────
@app.post("/api/generate-roadmap")
async def generate_roadmap(request: RoadmapRequest):
    try:
        model = CareerPathModel(model=request.model)
        roadmap = model.generate(
            user_skills=request.skills,
            job_description=request.job_description,
            designation=request.designation
        )

        # ── Save to MongoDB ──
        log = {
            "timestamp": datetime.utcnow(),
            "designation": request.designation,
            "skills": request.skills,
            "job_description": request.job_description,
            "model": request.model,
            "roadmap": roadmap,
        }
        await collection.insert_one(log)
        print("✅ Saved to MongoDB")

        return {"success": True, "roadmap": roadmap}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history(limit: int = 10):
    """Fetch last N roadmap generations"""
    cursor = collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    return {"success": True, "history": logs}


@app.get("/health")
def health():
    return {"status": "ok", "message": "Career GPS Backend Running 🚀"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)