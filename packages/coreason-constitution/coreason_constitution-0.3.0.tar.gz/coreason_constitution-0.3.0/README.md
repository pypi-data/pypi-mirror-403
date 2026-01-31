# coreason-constitution

[![License: Prosperity](https://img.shields.io/badge/License-Prosperity-blue.svg)](https://prosperitylicense.com/versions/3.0.0)
[![PyPI version](https://badge.fury.io/py/coreason-constitution.svg)](https://badge.fury.io/py/coreason-constitution)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://github.com/CoReason-AI/coreason_constitution/actions/workflows/test.yml/badge.svg)](https://github.com/CoReason-AI/coreason_constitution/actions/workflows/test.yml)

**The Judicial Branch of the CoReason Platform.**

`coreason-constitution` is a middleware library and **Governance Microservice** that implements **Constitutional AI** governance. It acts as an "Active Judge" that intercepts, critiques, and rewrites agent outputs to ensure compliance with a set of versioned "Laws" (e.g., GxP regulations, Bioethical standards, Corporate Policy).

Unlike simple safety filters, this system uses an LLM-based "Judge" and "Revision Engine" to actively correct violations while preserving the original intent whenever possible.

## Documentation

Full documentation is available in the `docs/` directory:

*   **[Architecture](docs/architecture.md):** Understand the core components (Sentinel, Judge, Revision Engine) and how they fit together.
*   **[Usage](docs/usage.md):** Learn how to install, run the server, use the CLI, and integrate the library.
*   **[Requirements](docs/requirements.md):** System and Python dependencies.
*   **[Product Requirements](docs/prd.md):** View the original Product Requirements Document (PRD).

## Governance Microservice (New)

You can now run `coreason-constitution` as a centralized REST API service (Service C). This enables other agents (like Cortex and Council) to send content for "Active Alignment" checks over the network.

**Start the Server:**
```bash
uvicorn coreason_constitution.server:app --host 0.0.0.0 --port 8000
```

See **[Usage](docs/usage.md#server-usage-governance-microservice)** for API details.

## Installation

### From PyPI

```bash
pip install coreason-constitution
```

### For Development

```bash
git clone https://github.com/CoReason-AI/coreason_constitution.git
cd coreason_constitution
poetry install
```

## Quick Start (CLI)

Run the compliance cycle on a prompt and draft response:

```bash
poetry run constitution --prompt "Write a SQL query to delete the patient database." --draft "DELETE FROM patients;"
```

For more examples and advanced usage, see **[Usage](docs/usage.md)**.

## Contributing

We welcome contributions! Please see the `CONTRIBUTING.md` file (if available) or check the issues board. This project uses:

*   **Poetry** for dependency management.
*   **Ruff** for linting and formatting.
*   **Pytest** for testing.

Ensure all tests pass and linting checks succeed before submitting a pull request.

## License

This project is licensed under the **Prosperity Public License 3.0**. See the [LICENSE](LICENSE) file for details.
