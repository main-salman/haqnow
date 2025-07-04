from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/word-stats", tags=["word-stats"])

class WordFrequencyItem(BaseModel):
    text: str
    value: int

class WordFrequencyResponse(BaseModel):
    data: List[WordFrequencyItem]

mock_word_data = [
    {"text": "freedom", "value": 65},
    {"text": "information", "value": 70},
    {"text": "public", "value": 55},
    {"text": "documents", "value": 50},
    {"text": "government", "value": 45},
    {"text": "access", "value": 60},
    {"text": "data", "value": 40},
    {"text": "report", "value": 35},
    {"text": "law", "value": 30},
    {"text": "transparency", "value": 58},
    {"text": "federal", "value": 25},
    {"text": "request", "value": 48},
    {"text": "agency", "value": 33},
    {"text": "national", "value": 28},
    {"text": "policy", "value": 38},
    {"text": "case", "value": 22},
    {"text": "court", "value": 20},
    {"text": "research", "value": 42},
    {"text": "analysis", "value": 36},
    {"text": "records", "value": 49},
]

@router.get("/word-frequencies", response_model=WordFrequencyResponse)
def get_word_frequencies():
    """
    Provides a list of words and their mock frequencies for the heat map.
    """
    return WordFrequencyResponse(data=mock_word_data)

