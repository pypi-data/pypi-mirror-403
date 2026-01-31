from typing import Any, Dict, List

try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

class NanoNER:
    """
    LNT Semantic Extraction Engine.
    Provides lightweight fuzzy semantic extraction.
    Ensures 100% local, low-latency execution.
    """
    _instance = None
    _initialized: bool
    
    def __new__(cls) -> "NanoNER":
        if cls._instance is None:
            cls._instance = super(NanoNER, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

    def extract_entities(self, text: str, labels: List[str]) -> Dict[str, Any]:
        """
        Extracts entities using fuzzy semantic matching and regex.
        Ideal for resource-constrained "Sovereign" environments.
        """
        extracted = {}
        import re
        
        # 1. Clean and tokenize text
        words = re.findall(r'\w+', text.lower())
        
        for entity_id in labels:
            natural_label = entity_id.replace("_", " ")
            
            # 2. Look for explicit mentions or fuzzy matches
            # We look for the entity name or its natural variation in the text
            if HAS_RAPIDFUZZ:
                # Find the best matching word/phrase for the entity label
                match = process.extractOne(natural_label, words, scorer=fuzz.WRatio)
                if match and match[1] > 80: # High confidence threshold
                    # Found a semantic hook, now look for the nearest number
                    pattern = rf"{re.escape(match[0])}\D*(\d+\.?\d*)"
                    res = re.search(pattern, text.lower())
                    if res:
                        extracted[entity_id] = float(res.group(1))
                        continue
            
            # 3. Fallback to standard heuristic if fuzzy matching missed
            pattern = rf"{re.escape(entity_id)}\D*(\d+\.?\d*)"
            res = re.search(pattern, text.lower())
            if res:
                extracted[entity_id] = float(res.group(1))
                
        return extracted
