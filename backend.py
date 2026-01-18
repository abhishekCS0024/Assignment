from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
from datetime import datetime

# Import your existing LinkedIn Growth Agent
from main import run_linkedin_growth_agent

app = FastAPI(title="LinkedIn Growth Agent API", version="1.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LinkedInRequest(BaseModel):
    description: str
    expertise: str
    audience: str

class LinkedInResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str

@app.post("/generate-content", response_model=LinkedInResponse)
async def generate_linkedin_content(request: LinkedInRequest):
    """Generate LinkedIn content plan"""
    try:
        # Run your existing agent
        result = run_linkedin_growth_agent(
            desc=request.description,
            expertise=request.expertise,
            audience=request.audience
        )
        
        return LinkedInResponse(
            success=True,
            data=result,
            message="Content generated successfully!"
        )
    except Exception as e:
        return LinkedInResponse(
            success=False,
            message=f"Error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Check if API is running"""
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)