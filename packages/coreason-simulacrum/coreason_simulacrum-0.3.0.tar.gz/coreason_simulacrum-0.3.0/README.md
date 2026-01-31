# coreason-simulacrum

> **The Adversarial Simulation & Chaos Engineering Engine for Coreason-AI.**

[![License: Prosperity 3.0](https://img.shields.io/badge/license-Prosperity%203.0-blue)](https://prosperitylicense.com/versions/3.0.0)
[![CI Status](https://github.com/CoReason-AI/coreason-simulacrum/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason-simulacrum/actions)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Documentation](https://img.shields.io/badge/docs-product_requirements-green)](docs/product_requirements.md)

**coreason-simulacrum** is the automated "Red Team" engine for the ecosystem, addressing the "Static Evaluation Trap" by evolving beyond benchmarks. It serves as a dual-engine simulator:

1.  **The Adversarial Engine (RL):** Dynamically evolves social engineering attacks using **TAP (Tree of Attacks with Pruning)**.
2.  **The Chaos Engine (Infra):** Injects latency, errors, and noise to verify GxP resilience.

---

## Features

-   **Dual-Agent Red Teaming:** Uses a "Strategist" (High-Reasoning) and "Attacker" (Uncensored) architecture.
-   **Evolutionary Attacks (TAP):** Optimizes attack trajectories over multiple turns to maximize success rates.
-   **Infrastructure Chaos:** Simulates latency, API errors, and token starvation to test resilience.
-   **Auto-Hardener:** Generates DPO triplets (Attack, Refusal, Compliance) from successful attacks for model fine-tuning.
-   **Model Diversity Enforcement:** Prevents model collapse by enforcing different families between Attacker and Target.
-   **Constitutional Inversion:** Inverts safety constitutions to generate boundary probes.

---

## Installation

```bash
pip install coreason-simulacrum
```

## Usage

coreason-simulacrum can be used as a Python library or as a standalone microservice.

### 1. Library / CLI Mode

See [docs/usage.md](docs/usage.md#1-library--cli-mode) for Python examples.

### 2. Server Mode (Microservice)

Run the simulation engine as a REST API (Service C) using Docker.

```bash
docker run -p 8000:8000 coreason-simulacrum
```

Send a simulation request:

```bash
curl -X POST "http://localhost:8000/simulate" \
     -H "Content-Type: application/json" \
     -d '{
           "type": "ADVERSARIAL_RL",
           "profile": {
             "name": "The Hacker",
             "goal": "Extract PII",
             "strategy_model": "gpt-4",
             "attack_model": "mistral-large"
           }
         }'
```

For detailed API documentation, see [docs/usage.md](docs/usage.md).

## License

This project is licensed under the **Prosperity Public License 3.0**.
Commercial use beyond a 30-day trial requires a separate license.
See the [LICENSE](LICENSE) file for details.
