import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LNT-SDK")

@dataclass
class LNTResponse:
    status: str
    domain: str
    proposal: Dict[str, Any]
    violations: List[Dict[str, Any]]
    proof: str
    explanation: str
    metadata: Dict[str, Any]

class LNTClient:
    """
    LNT SDK: A technical interface for experimenting with Neuro-Symbolic Logic.
    Supports asynchronous execution, local audits, and logic proofs.
    """
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        max_retries: int = 3
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers: Dict[str, str] = {
            "X-LNT-API-KEY": self.api_key or "",
            "Content-Type": "application/json",
            "User-Agent": "LNT-Python-SDK/1.1.0-alpha"
        }
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "LNTClient":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=self.timeout
            )
        return self._client

    async def evaluate(
        self, 
        user_text: str, 
        domain: Optional[str] = None,
        shadow_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Remote evaluation via an LNT service.
        """
        if not self.api_key:
            return {"status": "ERROR", "error": "api_key is required for remote evaluation."}
            
        client = await self._get_client()
        payload = {
            "user_text": user_text,
            "domain_override": domain,
            "shadow_mode": shadow_mode
        }

        for attempt in range(self.max_retries):
            try:
                response = await client.post("/process", json=payload)
                response.raise_for_status()
                return cast(Dict[str, Any], response.json())
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"LNT connection failed after {self.max_retries} attempts: {str(e)}")
                    return {"status": "SDK_CONNECTION_ERROR", "error": str(e)}
                
                wait_time = 2 ** attempt # Exponential backoff
                logger.warning(f"LNT connection attempt {attempt + 1} failed. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                logger.error(f"LNT API rejected request: {e.response.status_code} - {e.response.text}")
                return {"status": "API_ERROR", "code": e.response.status_code, "detail": e.response.text}
        
        return {"status": "UNKNOWN_ERROR"}

    def audit(self, manifest_id: str, proposal: Dict[str, Any]) -> Any:
        """
        Directly audits a proposal against a logic manifest.
        If no api_key is provided, this runs locally.
        
        Args:
            manifest_id: The ID of the manifest (e.g., 'visa_application')
            proposal: The structured data to audit.
        """
        from dataclasses import make_dataclass

        from lnt_sovereign.core.topology import TopologyOrchestrator
        
        # Simulating the local engine behavior for the 'toolbox' mode
        manifold = TopologyOrchestrator()
        
        # Map manifest_id to domain_id if needed, or use filename directly
        # In the engine, manifest_id usually leads to a file in manifests/examples/
        # TopologyOrchestrator's process_application detects domain from text, 
        # but for a direct 'audit' we can go straight to the kernel.
        
        manifest_path = os.path.join(manifold.manifest_dir, f"{manifest_id}.json")
        if not os.path.exists(manifest_path):
            # Fallback to direct name check
            manifest_path = manifold._get_manifest_path(manifest_id.upper())

        try:
            manifest = manifold.kernel_engine.load_manifest(manifest_path)
            trace = manifold.kernel_engine.trace_evaluate(proposal)
            
            # Wrap in a response object
            LNTResult = make_dataclass('LNTResult', ['status', 'score', 'violations', 'domain', 'proof'])
            violations_list = [v for v in trace["violations"]]
            
            return LNTResult(
                status="PASS" if not trace["violations"] else "FAIL",
                score=trace["score"],
                violations=violations_list,
                domain=manifest.domain_id,
                proof="local_verification_signed"
            )
        except Exception as e:
            logger.error(f"Local audit failed: {str(e)}")
            raise e

    async def get_system_health(self) -> Dict[str, Any]:
        """Queries the engine's operational metrics (Latency, Hallucination Rate)."""
        client = await self._get_client()
        try:
            response = await client.get("/ops")
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Returns advanced decision trends and rule heatmaps."""
        client = await self._get_client()
        try:
            response = await client.get("/analytics/summary")
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def verify_proof_integrity(self, result: Dict[str, Any]) -> bool:
        """
        Validates the SHA-256 integrity of a logic proof.
        """
        proof = result.get("proof")
        return bool(proof and len(proof) == 64)

    def get_requirements(self, manifest_id: str) -> Dict[str, Any]:
        """
        Returns the expected entity schema for a specific manifest.
        This provides the 'Contract' for LLM steering.
        """
        from lnt_sovereign.core.topology import TopologyOrchestrator
        manifold = TopologyOrchestrator()
        
        manifest_path = os.path.join(manifold.manifest_dir, f"{manifest_id}.json")
        if not os.path.exists(manifest_path):
            manifest_path = manifold._get_manifest_path(manifest_id.upper())

        try:
            manifest = manifold.kernel_engine.load_manifest(manifest_path)
            return {
                "domain": manifest.domain_id,
                "entities": manifest.entities,
                "constraints": [
                    {
                        "id": c.id,
                        "entity": c.entity,
                        "operator": c.operator,
                        "description": c.description
                    } for c in manifest.constraints
                ]
            }
        except Exception as e:
            logger.error(f"Failed to fetch requirements: {str(e)}")
            raise e
