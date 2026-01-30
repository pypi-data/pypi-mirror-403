"""Google Generative AI adapter for database analysis recommendations"""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class GoogleAIAdapter:
    """Adapter for Google Generative AI (Gemini) integration

    Provides methods to send database analysis to Google's Gemini model
    and receive structured recommendations.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash",
        stream: bool = False,
    ):
        """Initialize Google AI adapter

        Args:
            api_key: Google API key (from env GOOGLE_API_KEY if not provided)
            model: Gemini model to use (default: gemini-2.0-flash)
            stream: Whether to stream responses (default: False)

        Raises:
            ValueError: If API key not provided and not in env
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY env var or pass api_key."
            )

        self.model = model
        self.stream = stream

        # Lazy import to avoid hard dependency
        try:
            import google.generativeai as genai

            self.genai = genai
            genai.configure(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "google-generativeai not installed. "
                "Install with: pip install google-generativeai"
            )

    def analyze_postgresql(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> str:
        """Send PostgreSQL analysis prompt to Gemini

        Args:
            prompt: Formatted prompt with analysis data
            system_instruction: Optional system instruction for context

        Returns:
            Gemini's recommendations as string
        """
        return self._send_prompt(prompt, system_instruction)

    def analyze_mongodb(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> str:
        """Send MongoDB analysis prompt to Gemini

        Args:
            prompt: Formatted prompt with analysis data
            system_instruction: Optional system instruction for context

        Returns:
            Gemini's recommendations as string
        """
        return self._send_prompt(prompt, system_instruction)

    def _send_prompt(
        self, prompt: str, system_instruction: Optional[str] = None
    ) -> str:
        """Send prompt to Gemini and return response

        Args:
            prompt: User prompt with analysis data
            system_instruction: Optional system instruction

        Returns:
            Response text from Gemini

        Raises:
            Exception: On API errors or connection issues
        """
        try:
            model = self.genai.GenerativeModel(
                self.model,
                system_instruction=system_instruction,
            )

            if self.stream:
                return self._stream_response(model, prompt)
            else:
                response = model.generate_content(prompt)
                return response.text  # type: ignore

        except Exception as e:
            logger.error(f"Error calling Google AI API: {e}")
            raise

    def _stream_response(self, model: Any, prompt: str) -> str:
        """Stream response from Gemini and collect output

        Args:
            model: Generative model instance
            prompt: Prompt to send

        Returns:
            Collected response text
        """
        full_response = []
        response = model.generate_content(prompt, stream=True)

        for chunk in response:
            if chunk.text:
                full_response.append(chunk.text)
                # Optionally print chunks for live feedback
                print(chunk.text, end="", flush=True)

        print()  # New line after streaming
        return "".join(full_response)

    def is_available(self) -> bool:
        """Check if Google AI API is available and configured

        Returns:
            True if API key is set and library available, False otherwise
        """
        return bool(self.api_key)

    @staticmethod
    def get_available_models() -> list[str]:
        """Get list of available Gemini models

        Returns:
            List of model names (default available models)
        """
        return [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
