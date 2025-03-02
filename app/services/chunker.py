import math
from typing import List, Dict, Any

from app.utils.helpers import create_prompt

def determine_chunk_size(
    total_utterances: int, 
    target_chunks: int = 10, 
    min_chunk_size: int = 50, 
    max_chunk_size: int = 100
) -> int:
    """
    Determines the optimal chunk size for processing.
    
    Args:
        total_utterances: The total number of utterances in the transcript
        target_chunks: The target number of chunks to create
        min_chunk_size: The minimum chunk size
        max_chunk_size: The maximum chunk size
        
    Returns:
        The determined chunk size
    """
    # Calculate ideal chunk size to meet target_chunks
    ideal_chunk_size = math.ceil(total_utterances / target_chunks)
    
    # Ensure chunk size is within bounds
    return max(min(ideal_chunk_size, max_chunk_size), min_chunk_size)

def process_chunks(
    data: List[Dict[str, Any]],
    chunk_size: int,
    speakers: List[Dict[str, Any]],
    attendees: List[Dict[str, Any]],
    overlap: int = 5
) -> List[str]:
    """
    Processes the transcript data into overlapping chunks with prompts.
    
    Args:
        data: The transcript data (list of utterances)
        chunk_size: The size of each chunk
        speakers: The speakers data
        attendees: The attendees data
        overlap: The number of utterances to overlap between chunks
        
    Returns:
        A list of prompts for each chunk
    """
    prompts = []
    start = 0
    
    while start < len(data):
        # Calculate end position ensuring we don't exceed data length
        end = min(start + chunk_size, len(data))
        
        # Extract current chunk
        chunk = data[start:end]
        
        # Create prompt for the current chunk
        prompt = create_prompt(chunk, speakers, attendees)
        prompts.append(prompt)
        
        # Calculate next start position with overlap
        # If we're at the end, move by full chunk size to terminate the loop
        if start + chunk_size >= len(data):
            start += chunk_size
        else:
            # Otherwise, move forward by chunk_size - overlap
            start += chunk_size - overlap
    
    return prompts