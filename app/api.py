import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from app.cv_processing import proces_cv

app = FastAPI()

class AnalyzeRequest(BaseModel):
    fileUrl: str
    jobDescription: str

@app.post("/analyze")
async def analyze_cv(analyze_request: AnalyzeRequest):
   return proces_cv(analyze_request.fileUrl, analyze_request.jobDescription)
