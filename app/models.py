from pydantic import BaseModel, HttpUrl, Field, EmailStr
from typing import List, Dict, Optional, Any, Union
from datetime import datetime

# Request Models
class TranscriptRequest(BaseModel):
    """Request model for transcript URL endpoint."""
    transcript_url: HttpUrl = Field(
        ..., 
        description="URL to the JSON transcript file"
    )

class ProcessingOptions(BaseModel):
    """Options for transcript processing."""
    async_mode: bool = Field(
        False, 
        description="Process asynchronously and return a job ID"
    )
    ai_provider: str = Field(
        "openai", 
        description="AI provider to use (openai or anthropic)"
    )
    chunk_overlap: int = Field(
        5, 
        description="Number of utterances to overlap between chunks",
        ge=0,
        le=20
    )

# Transcript Data Models
class Speaker(BaseModel):
    """Model for a transcript speaker."""
    speakerId: str
    name: str

class Attendee(BaseModel):
    """Model for a meeting attendee."""
    attendeeId: str
    email: EmailStr

class Transcription(BaseModel):
    """Model for a single transcription entry."""
    transcriptionId: str
    speakerId: str
    text: str
    startTime: float
    endTime: float

class TranscriptData(BaseModel):
    """Model for complete transcript data."""
    transcriptions: List[Transcription]
    speakers: List[Speaker]
    attendees: List[Attendee]

# Response Models
class SummaryResponse(BaseModel):
    """Response model for synchronous summary requests."""
    final_summary: str
    clean_summaries: str

class ProcessingStatus(BaseModel):
    """Response model for asynchronous job status."""
    job_id: str
    status: str = Field(
        ..., 
        description="Status of the job (queued, processing, completed, failed)"
    )
    progress: Optional[float] = Field(
        None, 
        description="Progress of the job from 0.0 to 1.0",
        ge=0.0,
        le=1.0
    )
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# For API responses that could be either a summary or a job status
SummaryOrStatus = Union[SummaryResponse, ProcessingStatus]

# Internal Models
class Job(BaseModel):
    """Model for internal job tracking."""
    job_id: str
    status: str
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime