"""
Dream Analysis Service using Gemini NLP.
Analyzes dream journals for symbolism and recurring patterns over time.
"""

import json
from sqlalchemy.orm import Session
from models.journal import JournalEntry
from services.gemini_service import gemini_service

class DreamAnalyzer:
    def __init__(self):
        self.system_prompt = """
        You are a Jungian psychoanalyst and dream expert.
        Analyze the provided dream description and extract its core symbolism and meaning.
        
        Return ONLY a JSON object with this exact schema:
        {
            "dream_type": string, // One of: "lucid", "nightmare", "recurring", "anxiety", "processing", "prophetic", "normal"
            "symbols": [string], // 2-5 key symbols from the dream (e.g., "falling", "teeth falling out", "water")
            "interpretation": string // A 2-3 sentence psychological interpretation of what the dream might represent about the user's waking life state.
        }
        """

    def analyze_dream(self, content: str) -> dict:
        """Analyze a single dream journal entry."""
        prompt = f"Dream Description:\n{content}"
        
        try:
            response_text = gemini_service.generate_completion(
                user_query=prompt,
                system_prompt=self.interpretation_prompt,
                temperature=0.5 # A bit of creativity for dream interpretation
            )
            
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
                
            result = json.loads(cleaned.strip())
            return {
                "dream_type": result.get("dream_type", "normal"),
                "symbols": result.get("symbols", []),
                "interpretation": result.get("interpretation", "Unable to fully interpret.")
            }
        except Exception as e:
            return {
                "dream_type": "normal",
                "symbols": [],
                "interpretation": f"Analysis failed: {str(e)}"
            }

    def detect_recurring_patterns(self, db: Session, user_id: int) -> dict:
        """Scan a user's recent dreams to find overarching narrative or symbol patterns."""
        # Get last 10 entries that have dream data
        recent_dreams = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id,
            JournalEntry.dream_symbols != None
        ).order_by(JournalEntry.entry_date.desc()).limit(10).all()
        
        if len(recent_dreams) < 3:
            return {"status": "not_enough_data", "message": "Need at least 3 dream logs"}
            
        all_symbols = []
        for d in recent_dreams:
            if d.dream_symbols:
                all_symbols.extend(d.dream_symbols)
                
        # We could use Gemini here to summarize the `all_symbols` list
        # For now, a simple frequency count is effective enough to detect basic recurrence
        from collections import Counter
        counts = Counter(all_symbols)
        
        recurring = []
        for symbol, freq in counts.most_common(5):
            if freq >= 2: # Appeared in at least 2 dreams
                recurring.append({"symbol": symbol, "frequency": freq})
                
        return {
            "status": "success", 
            "total_dreams_analyzed": len(recent_dreams),
            "recurring_symbols": recurring,
            "pattern_summary": f"You frequently dream about {recurring[0]['symbol']}." if recurring else "Dreams are highly varied."
        }

dream_analyzer = DreamAnalyzer()
