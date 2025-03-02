import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Any
import os
from openai import OpenAI
from dotenv import load_dotenv

# Import prompts
import prompt

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AIClient(ABC):
    """Abstract base class for AI provider clients."""
    
    @abstractmethod
    async def generate_summary(self, prompt_text: str) -> str:
        """
        Generate a summary for a transcript chunk.
        
        Args:
            prompt_text: The prompt to send to the AI
            
        Returns:
            The generated summary
        """
        pass
    
    @abstractmethod
    async def generate_final_summary(self, summaries_text: str) -> str:
        """
        Generate a final summary from multiple chunk summaries.
        
        Args:
            summaries_text: The combined chunk summaries
            
        Returns:
            The final summary
        """
        pass

class OpenAIClient(AIClient):
    """Client for interacting with OpenAI's API."""
    
    def __init__(
        self,
        chunk_summary_model: str = "gpt-4o-2024-08-06",
        final_summary_model: str = "gpt-4o-2024-08-06"
    ):
        """
        Initialize the OpenAI client.
        
        Args:
            chunk_summary_model: Model to use for chunk summaries
            final_summary_model: Model to use for the final summary
        """
        # Validate API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is missing. Please set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI()
        self.chunk_summary_model = chunk_summary_model
        self.final_summary_model = final_summary_model
    
    async def generate_summary(self, prompt_text: str) -> str:
        """
        Generate a summary using OpenAI.
        
        Args:
            prompt_text: The prompt to send to the API
            
        Returns:
            The generated summary
            
        Raises:
            Exception: If the API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.chunk_summary_model,
                messages=[
                    {"role": "system", "content": prompt.system_message},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {str(e)}")
            raise
    
    async def generate_final_summary(self, summaries_text: str) -> str:
        """
        Generate a final summary using OpenAI.
        
        Args:
            summaries_text: The combined chunk summaries
            
        Returns:
            The final summary
            
        Raises:
            Exception: If the API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.final_summary_model,
                messages=[
                    {"role": "system", "content": prompt.final_system_message},
                    {"role": "user", "content": summaries_text}
                ],
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating final summary with OpenAI: {str(e)}")
            raise

# Commented out but available when needed
"""
class AnthropicClient(AIClient):
    '''Client for interacting with Anthropic's API.'''
    
    def __init__(
        self,
        chunk_summary_model: str = "claude-3-haiku-20240307",
        final_summary_model: str = "claude-3-5-sonnet-20240620"
    ):
        '''
        Initialize the Anthropic client.
        
        Args:
            chunk_summary_model: Model to use for chunk summaries
            final_summary_model: Model to use for the final summary
        '''
        # Validate API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is missing. Please set ANTHROPIC_API_KEY environment variable.")
        
        self.client = anthropic.Anthropic()
        self.chunk_summary_model = chunk_summary_model
        self.final_summary_model = final_summary_model
    
    async def generate_summary(self, prompt_text: str) -> str:
        '''
        Generate a summary using Anthropic.
        
        Args:
            prompt_text: The prompt to send to the API
            
        Returns:
            The generated summary
            
        Raises:
            Exception: If the API call fails
        '''
        try:
            message = self.client.messages.create(
                model=self.chunk_summary_model,
                max_tokens=4000,
                temperature=0,
                system=prompt.system_message,
                messages=[
                    {
                        "role": "user",
                        "content": prompt_text
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error generating summary with Anthropic: {str(e)}")
            raise
    
    async def generate_final_summary(self, summaries_text: str) -> str:
        '''
        Generate a final summary using Anthropic.
        
        Args:
            summaries_text: The combined chunk summaries
            
        Returns:
            The final summary
            
        Raises:
            Exception: If the API call fails
        '''
        try:
            message = self.client.messages.create(
                model=self.final_summary_model,
                max_tokens=8192,
                temperature=0,
                system=prompt.final_system_message,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": summaries_text
                            }
                        ]
                    }
                ],
                extra_headers={"anthropic-beta":"max-tokens-3-5-sonnet-2024-07-15"}
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error generating final summary with Anthropic: {str(e)}")
            raise
"""

def get_ai_client(provider: str = "openai") -> AIClient:
    """
    Factory function to get the appropriate AI client based on provider.
    
    Args:
        provider: The AI provider to use ("openai" or "anthropic")
        
    Returns:
        An instance of the appropriate AIClient subclass
        
    Raises:
        ValueError: If an unsupported provider is specified
    """
    if provider.lower() == "openai":
        return OpenAIClient()
    elif provider.lower() == "anthropic":
        # Uncomment when needed
        # return AnthropicClient()
        raise ValueError("Anthropic support is currently disabled. Please use OpenAI or enable Anthropic in the code.")
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")