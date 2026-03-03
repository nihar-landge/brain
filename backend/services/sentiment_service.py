"""
NLP Sentiment Analysis Service using Gemini.
Extracts structured emotions, topics, and cognitive distortions from journal entries.
"""

import json
from services.gemini_service import gemini_service

class SentimentService:
    def __init__(self):
        self.system_prompt = """
        You are an expert psychologist and NLP semantic analyzer.
        Analyze the provided journal entry and return ONLY a valid JSON object with the following schema:
        {
            "sentiment_score": float, // between -1.0 (extremely negative) and 1.0 (extremely positive)
            "sentiment_label": string, // one of: "positive", "negative", "neutral", "mixed"
            "emotions": [string], // list of 1-4 specific emotions (e.g., "joy", "anxiety", "frustration", "gratitude")
            "topics": [string], // list of 1-3 main topics discussed
            "cognitive_distortions": [string] // list of any cognitive distortions present (e.g., "all-or-nothing thinking", "catastrophizing"), or empty list
        }
        Return ONLY the raw JSON object, no markdown blocks, no text outside the JSON.
        """

    def analyze_entry(self, content: str) -> dict:
        """
        Analyze a journal entry and return structured sentiment data.
        Falls back to neutral values if Gemini fails.
        """
        try:
            prompt = f"Journal Entry:\n{content}"
            response_text = gemini_service.generate_completion(
                user_query=prompt,
                system_prompt=self.system_prompt,
                temperature=0.1  # Low temperature for consistent JSON output
            )
            
            # Clean up potential markdown formatting from Gemini
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
                
            result = json.loads(cleaned.strip())
            return {
                "sentiment_score": float(result.get("sentiment_score", 0.0)),
                "sentiment_label": str(result.get("sentiment_label", "neutral")),
                "emotions": list(result.get("emotions", [])),
                "topics": list(result.get("topics", [])),
                "cognitive_distortions": list(result.get("cognitive_distortions", []))
            }
        except Exception as e:
            # Fallback on error
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "neutral",
                "emotions": [],
                "topics": [],
                "cognitive_distortions": []
            }

sentiment_service = SentimentService()
