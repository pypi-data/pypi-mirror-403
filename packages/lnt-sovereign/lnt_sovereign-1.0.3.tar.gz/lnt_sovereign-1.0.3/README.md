# LNT: Logic Neutrality Tensor
**Deterministic Validation Layer for AI-Generated Intents**

## ⚖️ Overview (Open Source)
LNT is a high-performance neuro-symbolic engine designed to enforce deterministic symbolic constraints on probabilistic AI outputs. It provides sub-millisecond scaling and formal Z3 consistency verification for mission-critical validation in FinTech, HealthTech, and automated infrastructure.

**License**: MIT. This distribution contains the core engine and public example manifests.

## 🚀 Key Technical Specifications
*   **Vectorized Kernel (BELM)**: SIMD-accelerated logic manifold ($O(n)$ complexity).
*   **Symbolic CLI**: Deterministic verification for MLOps pipelines.
*   **Tiered Enforcement**: Threshold-based logic validation (Advisory vs. Hard Fail).
*   **Formal Verification**: SMT-based (Z3) manifest consistency analysis.

## 🛠️ Quick Start

### Installation
```bash
pip install lnt-sovereign
```

### User as a Logic Verification Tool (CLI)
Integrate LNT into your automated pipelines to verify behavioral consistency before deployment. See our [CI/CD Workflow Template](examples/mlops/lnt-sovereign.yml) for a ready-to-use GitHub Action.

```bash
# Soft Governance (Advisory Mode)
lnt check --manifest policy.json --input proposal.json --advisory

# Hard Enforcement (Fail if score is low or TOXIC rules violated)
lnt check --manifest policy.json --input proposal.json --fail-under 90 --fail-on-toxic
```

### Use as an SDK
```python
from lnt_sovereign.client import LNTClient

client = LNTClient()
result = client.audit(manifest_id="visa_application", proposal=proposal)
print(f"Validation Certified: Score {result.score}")
```

## 📜 Technical Documentation
For detailed architecture, API reference, and MLOps guides, visit the [Documentation Portal](docs/index.md).

*   [**MLOps Integration Guide**](docs/mlops_integration.md): How to set up LNT as a "Logic Gate" in CI/CD.
*   [**Technical Whitepaper**](docs/whitepaper.md): Mathematical foundations and benchmark distributions.
*   [**API Reference**](docs/api_reference.md): Complete parameter registry and error codes.

---
*Maintained for high-reliability AI system development.*
