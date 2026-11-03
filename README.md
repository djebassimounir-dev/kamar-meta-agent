# KAMAR-META-AGENT

**Project release:** 1.0.0 (standalone demonstration)  
**Project:** Evidence-Aware AI Audit Framework  
**Author:** Mounir Djebassi  
**License:** MIT

## Overview

KAMAR-META-AGENT is a prototype for structurally reviewing outputs from AI agents. It checks evidence references, reports declared contradictions, inspects execution traces, verifies artifact hashes, and produces JSON audit reports.

The project currently includes a standalone demonstration in `main.py` and a separate modular implementation under `src/`.

## Core capabilities

- **Evidence-reference checks:** Flags claims with missing or invalid references to supplied evidence.
- **Declared contradiction reporting:** Includes contradictions provided in the input; it does not discover contradictions automatically.
- **Execution-trace checks:** Validates the structure of trace events and their timestamps.
- **Artifact integrity:** Uses SHA-256 to compare a supplied file with an expected hash.
- **Audit reports:** Writes machine-readable JSON results.
- **Token ledger:** The modular code includes a SQLite ledger with HMAC-protected records, revocation, and single-use token consumption.

## Demonstration

Run the standalone demonstration:

```bash
python main.py
```

It demonstrates:

1. **Review:** A claim without a valid evidence reference receives `REVIEW`.
2. **Allow:** A claim with an existing evidence reference and a structurally valid trace receives `ALLOW`.
3. **Artifact integrity:** The correct SHA-256 hash is accepted and an incorrect hash is rejected.

The demonstration writes these reports to `reports/`:

- `reports/audit_report.json`
- `reports/final_demo_summary.json`

## Architecture

| Component | Responsibility |
|---|---|
| `main.py` | Standalone demonstration and validation scenarios |
| `src/inspector.py` | Modular evidence-reference, contradiction, trace, and artifact checks |
| `src/engine.py` | Orchestrates the modular inspector through `KamarEngine` |
| `src/ledger.py` | SQLite token ledger and HMAC integrity checks |
| `src/report_generator.py` | JSON report generation for the modular path |
| `tests/` | Automated tests, primarily for modules under `src/` |
| `reports/` | Generated demonstration reports |
| `kamar-meta-agent.ipynb` | Notebook walkthrough |

**Execution-path note:** `main.py` contains a standalone demonstration inspector. The modular path uses `KamarEngine` and `KamarInspector` under `src/`. These are separate paths in this release; the standalone demonstration is not routed through the modular engine.

**Version note:** Version `1.0.0` refers to the standalone demonstration. The modular `KamarEngine` currently reports `2.3-RC` in its result metadata.

## Installation

Requirements:

- Python 3.10 or newer
- Packages listed in `requirements.txt`

After publishing the repository, replace `<YOUR_GITHUB_REPOSITORY_URL>` with its actual GitHub URL, then run:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd kamar-meta-agent
python -m pip install -r requirements.txt
```

## Tests

Run the automated test suite from the project directory:

```bash
python -m pytest -v
```

**Latest recorded result:**

```text
10 passed, 1 warning
```

The 10 tests primarily exercise the modular components under `src/`. They do not provide full test coverage of the standalone demonstration path in `main.py`. The warning in the recorded run came from the locally installed third-party `dash.testing` pytest plugin and did not cause a test failure.

## Scope and limitations

KAMAR-META-AGENT checks structural consistency and traceability. An `ALLOW` decision means the implemented structural checks passed. It does **not** establish that:

- a claim is factually true;
- referenced evidence semantically proves a claim;
- all possible contradictions have been found; or
- an AI-generated result is free from hallucinations.

This is an audit and validation prototype, not a complete semantic verification or certification system.

## Project status

**Status:** Demonstration and validation prototype.

The project explores practical methods for evidence-aware inspection, traceability, artifact integrity, and review of AI-agent outputs.

## Author

**Mounir Djebassi**  
Independent Researcher  
Constantine, Algeria

- GitHub: [djebassimounir-dev](https://github.com/djebassimounir-dev)
- ORCID: [0009-0009-6871-7693](https://orcid.org/0009-0009-6871-7693)

## License

This project is distributed under the MIT License. See [`LICENSE`](LICENSE) for the full license text.
