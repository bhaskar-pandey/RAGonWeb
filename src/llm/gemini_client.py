"""
Gemini Client Wrapper
Native implementation using the google-genai SDK.
"""
import os
import logging
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiClient:
    """Wrapper for Google Gemini models using the native GenAI SDK."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemma-3-27b-it"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY must be provided via argument or environment variable.")

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini SDK initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Client: {e}")
            raise

    def generate(self, prompt: str, max_output_tokens: int = 512, candidate_count: int = 1) -> str:
        """
        Generates text based on the provided prompt.

        Args:
            prompt: The input text for the model.
            max_output_tokens: The maximum length of the response.
            candidate_count: Number of response variations to generate.

        Returns:
            The generated text string.
        """
        try:
            config = types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                candidate_count=candidate_count,
                temperature=0.7,
                top_p=0.95,
                top_k=40
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )

            # Return text safely; handles cases where safety filters might block output
            return response.text if response.text else "No content generated (check safety filters)."

        except Exception as e:
            logger.error(f"Gemini Generation Error: {e}")
            return f"Error during generation: {str(e)}"