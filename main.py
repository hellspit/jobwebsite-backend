from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from database import db_handler
import asyncio
from telegram_handler import start_telegram_client
import uvicorn
import threading

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobPost(BaseModel):
    id: int
    job_title: str
    company: str
    salary: Optional[str]
    location: Optional[str]
    apply_link: str
    year: str
    posted_at: str
    raw_text: Optional[str]

@app.on_event("startup")
async def startup_event():
    # Start the Telegram client in the background
    asyncio.create_task(start_telegram_client())

@app.get("/")
async def read_root():
    return {"message": "Job Notification API"}

@app.get("/jobs", response_model=List[JobPost])
async def get_jobs():
    jobs = await db_handler.get_jobs()
    return jobs

@app.get("/jobs/{year}", response_model=List[JobPost])
async def get_jobs_by_year(year: str):
    jobs = await db_handler.get_jobs(year)
    return jobs

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def run_telegram_bot():
    asyncio.run(start_telegram_client())

if __name__ == "__main__":
    # Start Telegram bot in a separate thread
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.start()
    
    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000) 