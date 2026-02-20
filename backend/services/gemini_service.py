"""
Gemini API Service - LLM for conversations and insights.
Includes retry logic with exponential backoff and fallback responses.
"""

import time
from typing import Optional

from config import GEMINI_API_KEY, LLM_MODEL
from utils.logger import log
from utils.prompts import (
    GENERATE_INSIGHT_PROMPT,
    EXPLAIN_PREDICTION_PROMPT,
    SUMMARIZE_ENTRIES_PROMPT,
)


class GeminiService:
    """
    Wrapper for Google Gemini API.
    Used for natural language understanding, response generation, and insights.
    """

    def __init__(self):
        self._model = None
        self._initialized = False
        self._model_name = LLM_MODEL or "gemini-2.5-flash"
        self._fallback_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
        ]

    def _ensure_initialized(self):
        """Lazy initialization of the Gemini model."""
        if self._initialized:
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_API_KEY)
            self._model = genai.GenerativeModel(self._model_name)
            self._initialized = True
            log.info(f"Gemini service initialized successfully ({self._model_name})")
        except Exception as e:
            log.error(f"Gemini initialization failed: {e}")

    def _try_fallback_model(self, prompt: str) -> Optional[str]:
        """Try alternate Gemini models when current model is quota-limited."""
        try:
            import google.generativeai as genai

            for model_name in self._fallback_models:
                if model_name == self._model_name:
                    continue
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    if response and getattr(response, "text", None):
                        self._model = model
                        self._model_name = model_name
                        log.warning(
                            f"Switched Gemini model to {model_name} after quota/rate issue"
                        )
                        return response.text
                except Exception:
                    continue
        except Exception:
            return None

        return None

    def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Generate content with retry logic and exponential backoff.
        Handles rate limits, timeouts, and API errors gracefully.
        """
        self._ensure_initialized()
        if not self._model:
            return self._fallback_response()

        for attempt in range(max_retries):
            try:
                response = self._model.generate_content(prompt)
                return response.text

            except Exception as e:
                error_str = str(e).lower()

                # Rate limit — exponential backoff
                if "429" in error_str or "rate" in error_str or "quota" in error_str:
                    fallback = self._try_fallback_model(prompt)
                    if fallback:
                        return fallback
                    wait_time = (2**attempt) * 1  # 1s, 2s, 4s
                    log.warning(
                        f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    continue

                # Timeout — retry once
                if "timeout" in error_str or "deadline" in error_str:
                    log.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return self._fallback_response()

                # Other API errors — don't retry
                log.error(f"Gemini API error: {e}")
                return self._fallback_response()

        # All retries exhausted
        log.error("All retries exhausted for Gemini API")
        return self._fallback_response()

    def _fallback_response(self) -> str:
        """Return fallback response when AI is unavailable."""
        return (
            "I'm temporarily unable to generate an AI response. "
            "Your data has been saved. Please try again in a moment."
        )

    def generate_response(
        self,
        user_query: str,
        context: str = "",
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a response using Gemini with context."""
        prompt_parts = []

        if system_prompt:
            prompt_parts.append(system_prompt)

        if context:
            prompt_parts.append(f"\n--- Context ---\n{context}\n--- End Context ---\n")

        prompt_parts.append(f"User: {user_query}")

        full_prompt = "\n".join(prompt_parts)
        return self._generate_with_retry(full_prompt)


    def generate_stream(
        self,
        user_query: str,
        context: str = "",
        system_prompt: Optional[str] = None,
    ):
        """Generate a streaming response using Gemini with context."""
        self._ensure_initialized()
        if not self._model:
            yield self._fallback_response()
            return
            
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(system_prompt)
        if context:
            prompt_parts.append(f"\n--- Context ---\n{context}\n--- End Context ---\n")
        prompt_parts.append(f"User: {user_query}")
        full_prompt = "\n".join(prompt_parts)

        try:
            response = self._model.generate_content(full_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            log.error(f"Streaming error: {e}")
            yield "\n[Error: Connection interrupted]"

    def generate_insight(self, data_summary: str) -> str:
        prompt = GENERATE_INSIGHT_PROMPT.format(data_summary=data_summary)
        return self._generate_with_retry(prompt)

    def explain_prediction(
        self,
        prediction_type: str,
        prediction_value: float,
        confidence: float,
        factors: list,
    ) -> str:
        """Generate natural language explanation of an ML prediction."""
        self._ensure_initialized()
        if not self._model:
            return f"Prediction: {prediction_value:.0%} ({prediction_type})"

        factors_str = "\n".join(f"- {f}" for f in factors)
        prompt = EXPLAIN_PREDICTION_PROMPT.format(
            prediction_type=prediction_type,
            prediction_value=prediction_value,
            confidence=confidence,
            factors_str=factors_str
        )
        return self._generate_with_retry(prompt)

    def summarize_entries(self, entries_text: str, period: str = "weekly") -> str:
        """Summarize journal entries."""
        prompt = SUMMARIZE_ENTRIES_PROMPT.format(
            period=period,
            entries_text=entries_text
        )
        return self._generate_with_retry(prompt)


# Singleton instance
gemini_service = GeminiService()
