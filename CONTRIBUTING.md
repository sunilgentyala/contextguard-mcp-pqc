# Contributing to ContextGuard-MCP-PQC

This repository holds the implementation artifacts (PoCs, benchmarks, risk scoring, framework code) for the ICSCSA 2026 paper on post-quantum security for the Model Context Protocol. Contributions that extend the framework or make the PoCs more realistic are welcome.

---

## Getting Set Up

```bash
git clone https://github.com/sunilgentyala/contextguard-mcp-pqc
cd contextguard-mcp-pqc
pip install -r requirements.txt
```

Optional, for live ML-KEM / ML-DSA benchmarks instead of reference values:

```bash
pip install oqs-python
```

Run the existing demos to confirm your environment works before changing anything:

```bash
python poc/hndl_demo.py
python poc/downgrade_demo.py
python benchmarks/pqc_bench.py
python risk/risk_assessment.py
python framework/hrs.py
```

---

## Where to Start

Check the [issues](https://github.com/sunilgentyala/contextguard-mcp-pqc/issues) labeled `good first issue` or `help wanted`. Standing areas of interest:

- **New vulnerability classes** beyond V1-V4 (transport, identity, auth floor, result integrity) — e.g. session resumption downgrade, MCP resource-URI spoofing
- **Live benchmark data** — replacing reference-paper latency numbers in `benchmarks/pqc_bench.py` with numbers from `oqs-python` on more hardware profiles (ARM, different TLS libraries)
- **RSP (Result Signature Policy) implementation** — Layer 4 in the architecture table has no code module yet, only the concept
- **Additional HRS scoring criteria** or a reference HRS certificate validator CLI
- **A minimal reference MCP server** that actually enforces HAF/HKF at the transport layer, rather than simulating the check

---

## What Makes a Good PR

- One vulnerability class, benchmark, or framework module per PR
- New PoCs stay in `poc/` and are runnable standalone with `python poc/your_demo.py`
- Cite the RFC 9794 construct or OWASP/NIST reference your change relates to, if applicable
- No changes to the paper text or figures through this repo — this repo is code artifacts only, not the manuscript

---

## What Not to Send

- Manuscript/paper file changes (this repo does not host the paper itself)
- Production cryptographic implementations claimed as "battle-tested" — PoC code here is explicitly for research and education, not deployment
- Large dependency additions without discussion first

---

## Questions

Open an issue and tag it with the layer or vulnerability class it relates to (e.g. `HAF`, `HKF`, `HRS`, `RSP`).
