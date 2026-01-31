# LNT (Logic Neutrality Tool)
**Experimental Neuro-Symbolic Validation Prototype**

> [!WARNING]
> **Experimental Status**: LNT is currently a research prototype in early-stage development. It has **not** been audited for security, has **no** third-party validation, and is **not** recommended for production use, especially in mission-critical financial or healthcare applications.

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Formal Verification: Z3](https://img.shields.io/badge/Verification-Z3%20SMT-orange.svg)](https://github.com/Z3Prover/z3)

LNT is a developer library exploring the use of **Neuro-Symbolic Validation** to bridge probabilistic model outputs with structured logical constraints. It provides a technical framework for experimenting with formal verification in AI pipelines.

---

## Technical Concept

The core hypothesis of LNT is that business rules can be represented as a mathematical manifold and validated using an SMT solver (Z3) and vectorized matrix operations (NumPy).

### Current Implementation Features (Alpha):
*   **Vectorized Logic Engine**: A NumPy-based implementation for evaluating constraints.
*   **SMT Solver Integration**: Experimental bridge to the Z3 solver for checking manifest consistency.
*   **Semantic Mapping**: A lightweight fuzzy-matching layer (`rapidfuzz`) for mapping unstructured text to logic entities.
*   **Fairness Auditing**: A basic implementation of the 80% rule for statistical parity analysis.

---

## Project Status

- **Audits**: None. This project has not undergone any formal security or logic audits.
- **Production Use**: None. There is no evidence of production deployment; it is intended for local experimentation and research.
- **Benchmarks**: Preliminary local benchmarks suggest sub-millisecond evaluation for simple rule sets, but these have not been independently verified or peer-reviewed.

---

## Exploration: Using the Validation Gate

```bash
# Developer install
pip install lnt-sovereign
```

### Basic Example (Research Prototype)

```python
from lnt_sovereign import LNTClient

# Initialize the local prototype
client = LNTClient(base_url="http://localhost:8000")

# Sample input for evaluation
proposal = {
    "amount": 450.0,
    "user_risk_score": 15,
}

# Evaluate against an experimental manifest
result = client.audit("test_policy", proposal)

print(f"Status: {result.status}")
print(f"Logic Health Score: {result.score}")
```

---

## Documentation (Work in Progress)

*   [**Proposed Architecture**](docs/architecture.md)
*   [**Technical FAQ**](docs/faq.md)
*   [**Roadmap & Evolution**](RE_PLATFORMING_PLAN.md)

*LNT: A technical exploration in deterministic AI validation.*
