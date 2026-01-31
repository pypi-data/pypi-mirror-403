from typing import Any, Dict, List

from lnt_sovereign.core.kernel import DomainManifest


class NeuralParser:
    """
    Simulates a Neural Perception layer for intent extraction and explanation.
    In production, this would interface with an LLM or specialized SLM.
    """
    def detect_domain(self, user_text: str) -> str:
        """
        Detects the logical domain from user input.
        """
        text = user_text.upper()
        
        if "CRS" in text or "EXPRESS ENTRY" in text:
            return "CRS_PROFILE_V1"
            
        if "VISA" in text or "PASSPORT" in text:
            return "VISA_APPLICATION_V1"
            
        clinical_keys = ["HEALTH", "HR", "BP", "SPO2", "VITALS", "PATIENT", "GLUCOSE"]
        if any(key in text for key in clinical_keys):
            return "HEALTHCARE_TRIAGE_V1"
            
        return "VISA_APPLICATION_V1" # Default fallback

    def parse_intent(self, user_text: str, manifest: DomainManifest) -> Dict[str, Any]:
        """
        Structural Adapter: Maps unstructured text to manifest entities.
        Uses local NanoNER for semantic extraction with a heuristic fallback.
        """
        from lnt_sovereign.core.nano_inference import NanoNER
        
        # 1. Attempt Semantic Extraction using local NanoNER
        nano = NanoNER()
        proposal = nano.extract_entities(user_text, manifest.entities)
        
        # 2. Heuristic Fallback for missing entities
        text = user_text.lower()
        for entity in manifest.entities:
            if entity not in proposal:
                if entity in text:
                    import re
                    matches = re.findall(rf"{entity}\D*(\d+\.?\d*)", text)
                    if matches:
                        proposal[entity] = float(matches[0])
            
        return proposal

    def generate_explanation(self, violations: List[Dict[str, Any]], domain: str) -> str:
        """
        Generates a natural language explanation for rejections.
        """
        if not violations:
            return "Application satisfies all sovereign constraints."
        
        reasons = [v["description"] for v in violations]
        return f"Application rejected within domain {domain} due to: " + "; ".join(reasons)
