"""
Helper utilities for the transcript summarizer.

This module contains utility functions used across the application.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def create_prompt(extracted_data: List[Dict[str, Any]], speakers: List[Dict[str, Any]], attendees: List[Dict[str, Any]]) -> str:
    """
    Creates a prompt for the AI model based on the transcript data.
    
    Args:
        extracted_data: The transcript data for a chunk
        speakers: The speakers data
        attendees: The attendees data
        
    Returns:
        The formatted prompt string
    """
    # Start with the transcribed data
    prompt = "Here is the transcribed data:\n\n"
    
    # Add each transcription entry
    for item in extracted_data:
        prompt += f"Transcription ID: {item['transcriptionId']}\n"
        prompt += f"Speaker ID: {item['speakerId']}\n"
        prompt += f"Text: {item['text']}\n"
        prompt += f"Start Time: {item['startTime']}\n"
        prompt += f"End Time: {item['endTime']}\n\n"
    
    # Add speaker information
    speaker_info = "\n".join([f"Speaker ID: {s['speakerId']}, Name: {s['name']}" for s in speakers])
    prompt += f"And the following is the speakers info:\n{speaker_info}\n\n"
    
    # Add attendee information
    attendee_info = "\n".join([f"Attendee ID: {a['attendeeId']}, Email: {a['email']}" for a in attendees])
    prompt += f"And the following is the attendee info:\n{attendee_info}"
    
    return prompt

def sanitize_transcript_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes transcript data by ensuring all required fields are present and properly formatted.
    
    Args:
        data: The raw transcript data
        
    Returns:
        The sanitized transcript data
        
    Raises:
        ValueError: If required fields are missing or improperly formatted
    """
    # Check for required top-level keys
    required_keys = ["transcriptions", "speakers", "attendees"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required field: {key}")
    
    # Ensure transcriptions is a list
    if not isinstance(data["transcriptions"], list):
        raise ValueError("'transcriptions' must be a list")
    
    # Ensure each transcription has required fields
    for i, transcription in enumerate(data["transcriptions"]):
        required_trans_fields = ["transcriptionId", "speakerId", "text", "startTime", "endTime"]
        for field in required_trans_fields:
            if field not in transcription:
                raise ValueError(f"Transcription at index {i} is missing required field: {field}")
        
        # Convert time fields to float if they're strings
        for time_field in ["startTime", "endTime"]:
            if isinstance(transcription[time_field], str):
                try:
                    transcription[time_field] = float(transcription[time_field])
                except ValueError:
                    raise ValueError(f"Invalid {time_field} value in transcription at index {i}")
    
    # Ensure speakers and attendees are lists
    for field in ["speakers", "attendees"]:
        if not isinstance(data[field], list):
            raise ValueError(f"'{field}' must be a list")
    
    # Ensure each speaker has required fields
    for i, speaker in enumerate(data["speakers"]):
        if "speakerId" not in speaker or "name" not in speaker:
            raise ValueError(f"Speaker at index {i} is missing required fields")
    
    # Ensure each attendee has required fields
    for i, attendee in enumerate(data["attendees"]):
        if "attendeeId" not in attendee or "email" not in attendee:
            raise ValueError(f"Attendee at index {i} is missing required fields")
    
    return data

def format_time(seconds: float) -> str:
    """
    Formats a time in seconds to a readable string (HH:MM:SS).
    
    Args:
        seconds: The time in seconds
        
    Returns:
        A formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"