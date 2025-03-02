import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import (
    TranscriptRequest, 
    SummaryResponse, 
    ProcessingStatus, 
    SummaryOrStatus,
    ProcessingOptions
)
from app.services.ai_client import get_ai_client
from app.services.summarizer import TranscriptSummarizer
from app.utils.helpers import sanitize_transcript_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for job status (use a proper DB in production)
jobs = {}

# Function to periodically clean up expired jobs
def cleanup_expired_jobs():
    """
    Remove expired jobs from the jobs dictionary.
    Expired jobs are those older than settings.JOB_EXPIRY_HOURS.
    """
    current_time = datetime.now()
    expiry_threshold = current_time - timedelta(hours=settings.JOB_EXPIRY_HOURS)
    
    # Identify expired jobs
    expired_job_ids = []
    for job_id, job_data in jobs.items():
        created_at = job_data.get("created_at")
        if created_at and datetime.fromisoformat(created_at) < expiry_threshold:
            expired_job_ids.append(job_id)
    
    # Remove expired jobs
    for job_id in expired_job_ids:
        del jobs[job_id]
    
    if expired_job_ids:
        logger.info(f"Cleaned up {len(expired_job_ids)} expired jobs")

# Function to update job status
def update_job_status(
    job_id: str, 
    status: str, 
    progress: Optional[float] = None, 
    result: Optional[Dict] = None,
    error: Optional[str] = None
):
    """
    Update the status of a job in the jobs dictionary.
    
    Args:
        job_id: The ID of the job to update
        status: The new status
        progress: Optional progress value (0.0 to 1.0)
        result: Optional result dictionary
        error: Optional error message
    """
    if job_id in jobs:
        if status:
            jobs[job_id]["status"] = status
        if progress is not None:
            jobs[job_id]["progress"] = progress
        if result is not None:
            jobs[job_id]["result"] = result
        if error is not None:
            jobs[job_id]["error"] = error
        
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

async def process_transcript_in_background(
    transcript_data: Dict, 
    job_id: str,
    ai_provider: str,
    chunk_overlap: int
):
    """
    Process a transcript in the background.
    
    Args:
        transcript_data: The transcript data
        job_id: The job ID for tracking progress
        ai_provider: The AI provider to use
        chunk_overlap: The number of utterances to overlap between chunks
    """
    try:
        # Get AI client
        ai_client = get_ai_client(ai_provider)
        
        # Initialize summarizer
        summarizer = TranscriptSummarizer(ai_client)
        
        # Process the transcript
        await summarizer.summarize(
            transcript_data, 
            job_id=job_id,
            update_progress_callback=update_job_status
        )
    except Exception as e:
        logger.error(f"Background task error: {str(e)}")
        update_job_status(job_id, "failed", error=str(e))

@app.post("/summarize_transcript/", response_model=SummaryOrStatus)
async def api_summarize_transcript(
    request: TranscriptRequest,
    options: ProcessingOptions = Depends(),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Summarize a transcript from a URL.
    
    Args:
        request: The request containing the transcript URL
        options: Processing options
        background_tasks: FastAPI background tasks
        
    Returns:
        Either the summary directly, or a job ID for async processing
    """
    try:
        # Clean up expired jobs
        cleanup_expired_jobs()
        
        # Fetch the transcript data
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(str(request.transcript_url))
            response.raise_for_status()
            transcript_data = response.json()
        
        # Sanitize and validate transcript data
        transcript_data = sanitize_transcript_data(transcript_data)
        
        if options.async_mode:
            # Generate a job ID and start processing in the background
            job_id = f"job-{int(time.time())}"
            jobs[job_id] = {
                "status": "queued",
                "progress": 0,
                "result": None,
                "error": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            background_tasks.add_task(
                process_transcript_in_background, 
                transcript_data, 
                job_id,
                options.ai_provider,
                options.chunk_overlap
            )
            
            return ProcessingStatus(
                job_id=job_id,
                status="queued",
                progress=0,
                created_at=datetime.fromisoformat(jobs[job_id]["created_at"]),
                updated_at=datetime.fromisoformat(jobs[job_id]["updated_at"])
            )
        else:
            # Get AI client
            ai_client = get_ai_client(options.ai_provider)
            
            # Initialize summarizer
            summarizer = TranscriptSummarizer(ai_client)
            
            # Synchronous processing
            final_summary, clean_summaries = await summarizer.summarize(transcript_data)
            
            return SummaryResponse(
                final_summary=final_summary,
                clean_summaries=clean_summaries
            )
    
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to fetch transcript data: {e}"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unavailable: {e}"
        )
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in response")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid JSON format in the response"
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in api_summarize_transcript: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

@app.post("/summarize_transcript_file/", response_model=SummaryOrStatus)
async def api_summarize_transcript_file(
    file: UploadFile = File(...),
    options: ProcessingOptions = Depends(),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Summarize a transcript from a file upload.
    
    Args:
        file: The uploaded transcript file
        options: Processing options
        background_tasks: FastAPI background tasks
        
    Returns:
        Either the summary directly, or a job ID for async processing
    """
    try:
        # Clean up expired jobs
        cleanup_expired_jobs()
        
        # Ensure the uploaded file is a .json file
        if file.content_type != 'application/json':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload a .json file."
            )

        # Read the uploaded file
        content = await file.read()
        
        try:
            transcript_data = json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid JSON format in the uploaded file."
            )

        # Sanitize and validate transcript data
        transcript_data = sanitize_transcript_data(transcript_data)
        
        if options.async_mode:
            # Generate a job ID and start processing in the background
            job_id = f"job-{int(time.time())}"
            jobs[job_id] = {
                "status": "queued",
                "progress": 0,
                "result": None,
                "error": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            background_tasks.add_task(
                process_transcript_in_background, 
                transcript_data, 
                job_id,
                options.ai_provider,
                options.chunk_overlap
            )
            
            return ProcessingStatus(
                job_id=job_id,
                status="queued",
                progress=0,
                created_at=datetime.fromisoformat(jobs[job_id]["created_at"]),
                updated_at=datetime.fromisoformat(jobs[job_id]["updated_at"])
            )
        else:
            # Get AI client
            ai_client = get_ai_client(options.ai_provider)
            
            # Initialize summarizer
            summarizer = TranscriptSummarizer(ai_client)
            
            # Synchronous processing
            final_summary, clean_summaries = await summarizer.summarize(transcript_data)
            
            return SummaryResponse(
                final_summary=final_summary,
                clean_summaries=clean_summaries
            )
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in api_summarize_transcript_file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/job/{job_id}", response_model=ProcessingStatus)
async def get_job_status(job_id: str):
    """
    Get the status of an asynchronous job.
    
    Args:
        job_id: The job ID
        
    Returns:
        The job status
    """
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    job_data = jobs[job_id]
    
    return ProcessingStatus(
        job_id=job_id,
        status=job_data["status"],
        progress=job_data["progress"],
        result=job_data["result"],
        error=job_data["error"],
        created_at=datetime.fromisoformat(job_data["created_at"]) if "created_at" in job_data else None,
        updated_at=datetime.fromisoformat(job_data["updated_at"]) if "updated_at" in job_data else None
    )

@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
def root():
    """
    Root endpoint with API information.
    
    Returns:
        API information
    """
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "docs_url": "/docs",
        "health_check": "/health"
    }