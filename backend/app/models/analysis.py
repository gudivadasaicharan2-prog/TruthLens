from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from datetime import datetime
from app.core.database import Base


class AnalysisResult(str, enum.Enum):
    REAL = "Real"
    FAKE = "Fake"
    SUSPICIOUS = "Suspicious"


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class FactCheckStatus(str, enum.Enum):
    TRUE = "True"
    FALSE = "False"
    PARTIALLY_FALSE = "Partially False"
    UNVERIFIED = "Unverified"


class NewsAnalysis(Base):
    __tablename__ = "news_analyses"

    analysis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    news_title = Column(Text, nullable=False)
    news_content = Column(Text, nullable=False)
    news_url = Column(String, nullable=True)
    result = Column(SQLEnum(AnalysisResult), nullable=False)
    confidence = Column(Float, nullable=False)
    reasons = Column(JSON, nullable=True)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class MediaAnalysis(Base):
    __tablename__ = "media_analyses"

    media_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    file_type = Column(SQLEnum(MediaType), nullable=False)
    file_path = Column(String, nullable=True)
    result = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    analysis_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FactCheck(Base):
    __tablename__ = "fact_checks"

    check_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    claim = Column(Text, nullable=False)
    status = Column(SQLEnum(FactCheckStatus), nullable=False)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
