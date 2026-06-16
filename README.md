# ContextGuard-MCP-PQC

**Post-Quantum Security Framework for Model Context Protocol Using ContextGuard**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![IEEE Conference](https://img.shields.io/badge/Paper-IEEE_ICSCSA_2026-red.svg)](#citation)

Implementation artifacts for the ICSCSA 2026 paper presenting the first systematic application of RFC 9794 Post-Quantum/Traditional hybrid terminology to MCP's four security-relevant layers, and the ContextGuard-MCP-PQC governance framework.

---

## Paper

**Title:** Post-Quantum Security Framework for Model Context Protocol Using ContextGuard

**Authors:**
1. Sunil Gentyala -- HCLTech, Dallas TX, USA (IEEE Senior Member #101760715)
2. A.V.H Sai Prasad -- CMR Technical Campus, Hyderabad, India
3. Kommana Swathi -- Sir C R Reddy College of Engineering, Eluru, India
4. Vamshi Lande -- Research Student, University of North Texas, Denton TX, USA
5. Akhila Kasturi -- Research Analyst, HCLTech, USA

**Conference:** International Conference on Smart Computing and Systems Applications (ICSCSA) 2026

---

## Repository Contents

```
contextguard-mcp-pqc/
├── poc/
│   ├── hndl_demo.py          Harvest-Now-Decrypt-Later threat simulation
│   └── downgrade_demo.py     TLS cipher suite downgrade attack demo
├── benchmarks/
│   ├── pqc_bench.py          ML-KEM / ML-DSA performance benchmarks
│   └── results/              Benchmark output (CSV + JSON)
├── risk/
│   └── risk_assessment.py    Quantitative vulnerability risk scoring
├── framework/
│   ├── haf.py                Hybrid Authentication Floor (Layer 1)
│   └── hrs.py                Hybrid Readiness Score calculator (Layer 3)
├── CITATION.cff
├── LICENSE
└── README.md
```

---

## Framework Architecture

ContextGuard-MCP-PQC extends the base ContextGuard zero-trust governance architecture with a post-quantum control plane aligned to RFC 9794 constructs.

| Layer | MCP Security Surface | RFC 9794 Construct | ContextGuard Control |
|-------|---------------------|-------------------|----------------------|
| 1 | Host authentication | PQ/T hybrid digital signature | HAF (Hybrid Authentication Floor) |
| 2 | Transport channel | PQ/T composite KEM | HKF (Hybrid KEM Floor) |
| 3 | Server/tool identity | PQ/T parallel PKI | HRS (Hybrid Readiness Score) |
| 4 | Tool result integrity | PQ/T hybrid signature | RSP (Result Signature Policy) |

---

## Vulnerability Classes

| ID | Name | RFC 9794 Gap | Risk Level | Control |
|----|------|-------------|------------|---------|
| V1 | Absent Hybrid KEM in Transport | No composite KEM requirement | HIGH | HKF |
| V2 | Single-Algorithm Server Identity | No parallel PKI framework | HIGH | HRS |
| V3 | No Hybrid Auth Floor | No hybrid signature requirement | HIGH | HAF |
| V4 | Unsigned Tool Results | No hybrid result signature standard | HIGH | RSP |

---

## Quick Start

```bash
git clone https://github.com/sunilgentyala/contextguard-mcp-pqc
cd contextguard-mcp-pqc
pip install -r requirements.txt

# Run HNDL threat demonstration
python poc/hndl_demo.py

# Run downgrade attack demonstration
python poc/downgrade_demo.py

# Run performance benchmarks
python benchmarks/pqc_bench.py

# Run risk assessment
python risk/risk_assessment.py

# Run HRS calculator demo
python framework/hrs.py
```

Optional: For live ML-KEM / ML-DSA benchmarks, install liboqs-python:
```bash
pip install oqs-python
```

---

## Performance Summary

Reference values from Olushola and Meenakshi (Frontiers in Physics, 2026,
DOI: 10.3389/fphy.2025.1723966) and Halak et al. (MDPI Cryptography, 2024,
DOI: 10.3390/cryptography8020021):

| Algorithm | Operation | Mean Latency | vs. Classical |
|-----------|-----------|--------------|--------------|
| ML-KEM-768 | Encapsulation | 0.073 ms | 2.4x X25519 |
| ML-DSA-65 | Sign | 0.148 ms | 12x faster than RSA-2048 |
| X25519 + ML-KEM-768 | TLS handshake overhead | ~1.84 ms additional | < 1.5% of RTT |

Composite hybrid TLS handshake adds approximately 2,272 bytes of overhead per
connection (Stebila et al., draft-ietf-tls-hybrid-design-12, 2025).

---

## HRS Certificate Scoring Criteria

| Criterion | Description | Points |
|-----------|-------------|--------|
| HRS-1 | Leaf certificate has any PQ public key component | 1 |
| HRS-2 | Leaf certificate is PQ/T hybrid | 1 |
| HRS-3 | All intermediate CAs are PQ/T hybrid | 1 |
| HRS-4 | Root CA is PQ/T hybrid or PQ-only | 1 |
| HRS-5 | Downgrade protection active (HAF/HKF enforced) | 1 |

Score 0 = Traditional-only (Priority 1, immediate action). Score 5 = Fully hybrid.

---

## Citation

```bibtex
@inproceedings{gentyala2026contextguard_pqc,
  title     = {Post-Quantum Security Framework for Model Context Protocol Using ContextGuard},
  author    = {Gentyala, Sunil and Sai Prasad, A.V.H. and Swathi, Kommana
               and Lande, Vamshi and Kasturi, Akhila},
  booktitle = {Proceedings of the International Conference on Smart Computing
               and Systems Applications (ICSCSA)},
  year      = {2026},
  url       = {https://github.com/sunilgentyala/contextguard-mcp-pqc}
}
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

This repository contains implementation artifacts and proof-of-concept
demonstrations for academic research. The PoC code in `poc/` is for
educational purposes only.
