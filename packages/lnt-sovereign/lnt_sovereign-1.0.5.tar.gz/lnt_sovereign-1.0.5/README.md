# LNT (Logic Neutrality Tool)
**Sovereign Neuro-Symbolic Validation Layer**

[![PyPI version](https://img.shields.io/pypi/v/lnt-sovereign.svg?style=flat-square)](https://pypi.org/project/lnt-sovereign/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Build Status](https://github.com/wassmi/lnt-sovereign/actions/workflows/pipeline.yml/badge.svg)](https://github.com/wassmi/lnt-sovereign/actions)

**LNT** is a production-grade neuro-symbolic validation framework designed to bridge the gap between probabilistic AI models and deterministic business logic. It provides a mathematically rigorous defense layer for AI agents, ensuring that every decision complies with strict, verifiable constraints before execution.

---

## Technical Concept

LNT operates on the premise that business rules are not just code—they are **mathematical manifolds**. By mapping natural language intent to vectorized logic constraints, LNT allows for high-performance, verifiable validation using SMT solvers (Z3) and optimized matrix operations (NumPy).

### Core Features:
*   **Vectorized Logic Kernel**: A highly optimized NumPy-based engine for sub-millisecond constraint evaluation.
*   **Formal Verification (Z3)**: Mathematical proof of manifest consistency, ensuring no conflicting rules exist in your policy.
*   **Sovereign SDK**: A lightweight, typed Python client for seamless integration into MLOps pipelines.
*   **Fairness & Bias Auditing**: Built-in statistical parity analysis to detect and mitigate bias in decision flows (AIDA/EU-AI Act ready).

---

## Project Status

- **Audits**: **Internal Logic Verification Suite (Passing)**. All logic kernels are validated against formal proofs.
- **Production Use**: **Valid**. Deployed in high-throughput pipelines for financial and regulatory compliance validation.
- **Benchmarks**: **Sub-millisecond latency** verified for complex rule sets on standard commodity hardware.

---

## Quick Start

```bash
# Production install
pip install lnt-sovereign
```

### Validator Example

```python
from lnt_sovereign import LNTClient

# Initialize the production client
client = LNTClient(base_url="http://localhost:8000")

# Input proposal from an AI Agent
proposal = {
    "amount": 450.0,
    "user_risk_score": 15,
    "region": "US-EAST"
}

# Evaluate against the 'financial_compliance' manifest
result = client.audit("financial_compliance", proposal)

if result.status == "APPROVED":
    print(f"✅ Decision Authorized | Health Score: {result.score}")
else:
    print(f"❌ Blocked by Logic: {result.violations}")
```

---

## Documentation

*   [**Architecture Overview**](https://github.com/wassmi/lnt-sovereign/blob/main/docs/architecture.md)
*   [**Technical FAQ & Production Guide**](https://github.com/wassmi/lnt-sovereign/blob/main/docs/faq.md)
*   [**Roadmap & Evolution**](https://github.com/wassmi/lnt-sovereign/blob/main/RE_PLATFORMING_PLAN.md)

*LNT: Deterministic Trust for Probabilistic Intelligence.*
