from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.analysis import AnalysisResult, MediaType, FactCheckStatus


class NewsAnalysisRequest(BaseModel):
    title: str
    content: str
    url: Optional[str] = None


class NewsAnalysisResponse(BaseModel):
    result: AnalysisResult
    confidence: float
    reasons: List[str]
    sources: List[Dict[str, Any]]
    analysis_id: str


class ImageAnalysisResponse(BaseModel):
    authenticity_score: float
    deepfake_probability: float
    issues: List[str]
    heatmap_url: Optional[str] = None
    analysis_id: str


class VideoAnalysisRequest(BaseModel):
    url: Optional[str] = None


class VideoAnalysisResponse(BaseModel):
    result: str
    confidence: float
    suspicious_timestamps: List[float]
    frame_results: List[Dict[str, Any]]
    issues: List[str]
    analysis_id: str


class AudioAnalysisResponse(BaseModel):
    result: str
    confidence: float
    issues: List[str]
    analysis_id: str


class FactCheckRequest(BaseModel):
    claim: str


class FactCheckResponse(BaseModel):
    status: FactCheckStatus
    sources: List[Dict[str, Any]]
    similarity_scores: List[float]


class DashboardStats(BaseModel):
    total_analyses: int
    fake_detected: int
    deepfakes: int
    active_users: int


class DailyDetection(BaseModel):
    date: str
    count: int


class ContentTypeBreakdown(BaseModel):
    content_type: str
    count: int


class AnalysisHistory(BaseModel):
    analysis_id: str
    type: str
    result: str
    confidence: float
    created_at: datetime
