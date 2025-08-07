from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
import certifi
import os
from pymongo import MongoClient


# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
try:
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

    # Use certifi only if you're using MongoDB Atlas (mongodb+srv://)
    if "mongodb+srv" in mongo_url:
        client = MongoClient(mongo_url, tlsCAFile=certifi.where())
    else:
        client = MongoClient(mongo_url)

    db_name = os.environ.get('DB_NAME', 'dev404_music')
    db = client[db_name]
    emails_collection = db.emails
    print(f"✅ Connected to MongoDB: {mongo_url}")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")

    
# Pydantic models
class EmailSignup(BaseModel):
    email: EmailStr
    name: str = None

class EmailResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

@app.get("/")
async def root():
    return {"message": "DEV 404 Music API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "dev404-music-api"}

@app.post("/api/signup", response_model=dict)
async def signup_email(email_data: EmailSignup):
    """Sign up for DEV 404 fanbase"""
    try:
        # Check if email already exists
        existing = emails_collection.find_one({"email": email_data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new signup entry
        signup_entry = {
            "id": str(uuid.uuid4()),
            "email": email_data.email,
            "name": email_data.name or "Fan",
            "created_at": datetime.utcnow(),
        }
        
        # Insert to database
        result = emails_collection.insert_one(signup_entry)
        
        if result.inserted_id:
            return {
                "message": "Successfully joined the DEV 404 fanbase!",
                "email": email_data.email,
                "id": signup_entry["id"]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save email")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in signup_email: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/signups/count")
async def get_signups_count():
    """Get total number of signups"""
    try:
        count = emails_collection.count_documents({})
        return {"count": count}
    except Exception as e:
        print(f"Error getting signups count: {e}")
        return {"count": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

    import requests

# New route to fetch merch from Printful
@app.get("/api/merch")
async def get_merch():
    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('PRINTFUL_API_KEY')}"
        }
        response = requests.get("https://api.printful.com/store/products", headers=headers)
        data = response.json()

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=data.get("error", "Unknown error"))

        return data["result"]
    except Exception as e:
        print(f"Error fetching merch: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch merch from Printful")
