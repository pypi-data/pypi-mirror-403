import hashlib
import json
import os
import time
from typing import Any, Dict, List

from lnt_sovereign.core.analytics import LNTAnalyticsEngine
from lnt_sovereign.core.bias import BiasAuditor
from lnt_sovereign.core.compiler import LNTCompiler
from lnt_sovereign.core.feedback import FeedbackFlywheel
from lnt_sovereign.core.kernel import DomainManifest, KernelEngine
from lnt_sovereign.core.monitor import LNTMonitor
from lnt_sovereign.core.neural import NeuralParser
from lnt_sovereign.core.optimized_kernel import OptimizedKernel
from lnt_sovereign.core.state import LNTStateBuffer
from lnt_sovereign.core.telemetry import TelemetryManager


class TopologyOrchestrator:
    """
    Topology Orchestrator logic.
    Manages logic evaluation by loading domain-specific Manifests.
    Uses OptimizedKernel for logic enforcement.
    """
    def __init__(self) -> None:
        self.state_buffer = LNTStateBuffer()
        self.parser: NeuralParser = NeuralParser()
        self.kernel_engine: KernelEngine = KernelEngine(state_buffer=self.state_buffer)
        self.compiler: LNTCompiler = LNTCompiler()
        self.flywheel: FeedbackFlywheel = FeedbackFlywheel()
        self.monitor: LNTMonitor = LNTMonitor()
        self.analytics = LNTAnalyticsEngine(self.monitor)
        self.bias_auditor: BiasAuditor = BiasAuditor()
        self._compiled_cache: Dict[str, OptimizedKernel] = {} # domain_id -> OptimizedKernel
        
        # Professional distribution path resolution
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.manifest_dir = os.path.join(base_dir, "manifests", "examples")

    def process_application(self, user_text: str) -> Dict[str, Any]:
        """
        Unified logic loop with temporal and weighted evaluation.
        """
        # 1. Agnostic Domain Detection
        domain_key: str = self.parser.detect_domain(user_text)
        manifest_file: str = self._get_manifest_path(domain_key)
        
        # 2. Load Manifest & Original Logic (Interpreted path for temporal logic)
        try:
            manifest: DomainManifest = self.kernel_engine.load_manifest(manifest_file)
        except Exception as e:
            return {"status": "KERNEL_ERROR", "error": f"Failed to load manifest for {domain_key}: {str(e)}"}

        # 3. Dynamic Neural Perception (Proposal)
        neural_proposal: Dict[str, Any] = self.parser.parse_intent(user_text, manifest)

        # 4. Logical Evaluation (State-Aware)
        # We use the KernelEngine for core features (DAGs, Weights, Temporal)
        start_time = time.time()
        trace_result = self.kernel_engine.trace_evaluate(neural_proposal)
        latency_ms = (time.time() - start_time) * 1000.0
        
        violations: List[Dict[str, Any]] = trace_result["violations"]
        passes: List[str] = trace_result["passes"]
        score: float = trace_result["score"]
        is_safe: bool = len(violations) == 0
        
        status: str = "CERTIFIED" if is_safe else "REJECTED_BY_LOGIC"
        
        # 5. Audit Proof & Metadata
        proof_data: Dict[str, Any] = {
            "user_text": user_text, 
            "proposal": neural_proposal, 
            "status": status, 
            "domain": manifest.domain_id,
            "score": score,
            "passes": passes
        }
        proof_hash: str = hashlib.sha256(json.dumps(proof_data, sort_keys=True).encode('utf-8')).hexdigest()

        # Monitoring & Feedback
        self.monitor.log_transaction(
            domain=domain_key, 
            is_safe=is_safe,
            score=score,
            violations=violations,
            latency_ms=latency_ms
        )
        
        # Phase 4 Telemetry
        TelemetryManager().log_event(
            command="manifold_process",
            success=is_safe,
            latency_ms=latency_ms,
            metadata={"domain": manifest.domain_id, "score": score}
        )
        if not is_safe:
            self.flywheel.log_rejection(manifest.domain_id, neural_proposal, violations)

        return {
            "status": status,
            "domain": manifest.domain_id,
            "score": score,
            "proposal": neural_proposal,
            "violations": violations,
            "passes": passes,
            "proof": proof_hash,
            "explanation": self.parser.generate_explanation(violations, domain=domain_key)
        }

    def _get_manifest_path(self, domain_key: str) -> str:
        mapping: Dict[str, str] = {
            "VISA_APPLICATION_V1": "visa_application.json",
            "CRS_PROFILE_V1": "crs_profile.json",
            "HEALTHCARE_TRIAGE_V1": "healthcare_triage.json"
        }
        filename = mapping.get(domain_key, "visa_application.json")
        return os.path.join(self.manifest_dir, filename)
