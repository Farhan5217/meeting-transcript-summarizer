import logging
import asyncio
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from app.services.chunker import determine_chunk_size, process_chunks
from app.services.ai_client import AIClient
from app.utils.helpers import create_prompt

# Configure logging
logger = logging.getLogger(__name__)

class TranscriptSummarizer:
    """
    Service for summarizing meeting transcripts by breaking them into chunks 
    and processing them with AI.
    """
    
    def __init__(self, ai_client: AIClient):
        """
        Initialize the summarizer with an AI client.
        
        Args:
            ai_client: An instance of AIClient for generating summaries
        """
        self.ai_client = ai_client
    
    async def summarize(
        self, 
        transcript_data: Dict, 
        job_id: Optional[str] = None,
        update_progress_callback=None
    ) -> Tuple[str, str]:
        """
        Summarize a transcript by breaking it into chunks and then combining the summaries.
        
        Args:
            transcript_data: The transcript data containing transcriptions, speakers, and attendees
            job_id: Optional job ID for tracking progress
            update_progress_callback: Optional callback function to update job progress
            
        Returns:
            A tuple of (final_summary, clean_summaries)
            
        Raises:
            Exception: If any step of the summarization process fails
        """
        try:
            # Extract data
            utterances = transcript_data['transcriptions']
            speakers = transcript_data['speakers']
            attendees = transcript_data['attendees']
            total_utterances = len(utterances)
            
            # Update progress if callback provided
            if update_progress_callback and job_id:
                update_progress_callback(job_id, "processing", 0.1)
            
            # Determine chunk size based on total utterances
            chunk_size = determine_chunk_size(total_utterances)
            logger.info(f"Total utterances: {total_utterances}")
            logger.info(f"Using chunk size: {chunk_size}")
            
            # Process transcript into chunks with prompts
            chunk_prompts = process_chunks(utterances, chunk_size, speakers, attendees)
            summaries = []
            
            # Process each chunk
            for i, prompt in enumerate(chunk_prompts, 1):
                logger.info(f"Generating summary for chunk {i} of {len(chunk_prompts)}...")
                
                # Generate summary for the chunk
                summary = await self.ai_client.generate_summary(prompt)
                summaries.append(summary)
                logger.info(f"Summary {i} generated.")
                
                # Update progress if callback provided
                if update_progress_callback and job_id:
                    progress = 0.1 + (0.7 * (i / len(chunk_prompts)))
                    update_progress_callback(job_id, "processing", progress)
            
            # Combine all chunk summaries
            clean_summaries = "\n\n".join([f"Summary {i+1}:\n\n{summary}" for i, summary in enumerate(summaries)])
            
            logger.info("Generating final summary...")
            
            # Generate the final comprehensive summary
            final_summary = await self.ai_client.generate_final_summary(clean_summaries)
            
            # Update progress if callback provided
            if update_progress_callback and job_id:
                update_progress_callback(
                    job_id, 
                    "completed", 
                    1.0, 
                    result={
                        "final_summary": final_summary,
                        "clean_summaries": clean_summaries
                    }
                )
            
            return final_summary, clean_summaries
            
        except Exception as e:
            logger.error(f"Error in summarize_transcript: {str(e)}")
            
            # Update progress if callback provided
            if update_progress_callback and job_id:
                update_progress_callback(job_id, "failed", None, error=str(e))
            
            raise