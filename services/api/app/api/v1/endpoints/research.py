from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.session import get_db
from app.services.research_service import research_service

router = APIRouter()


class ResearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, description="User research question")


class ResearchSourceCitation(BaseModel):
    title: str
    publisher: str
    date: str
    url: str


class ResearchQueryResponse(BaseModel):
    question: str
    answer: str
    facts: List[str]
    sources: List[ResearchSourceCitation]
    caveat: str


@router.post("/query", response_model=ResearchQueryResponse)
def query_research_assistant(payload: ResearchQueryRequest, db: Session = Depends(get_db)):
    """
    Query the AI Research Assistant for evidence-backed financial analysis,
    sanitized against prompt injection and grounded strictly in verified database records.
    """
    result = research_service.answer_query(db, payload.query)
    return result

