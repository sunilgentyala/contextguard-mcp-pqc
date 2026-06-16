"""
Hybrid Readiness Score (HRS) Calculator - ContextGuard-MCP-PQC
Layer 3: Server and Tool Identity Certificate Evaluation

Assigns a 0-5 integer score to each MCP server endpoint reflecting
its certificate chain quantum posture. The score drives migration
priority queue ordering in Phase 1 (Inventory and Assessment).

Scoring criteria (each criterion adds 1 point):
  HRS-1: Leaf certificate contains a post-quantum public key component
  HRS-2: Leaf certificate is PQ/T hybrid (both PQ and traditional keys present)
  HRS-3: Intermediate CA(s) contain PQ/T hybrid keys (no classical-only CAs)
  HRS-4: Root CA is a PQ/T hybrid or post-quantum-only root
  HRS-5: Downgrade protection verified at protocol negotiation layer (HAF/HKF)

A score of 0 means the entire chain is traditional-only.
A score of 5 means full hybrid coverage from leaf through root with enforcement.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class CertKeyType(Enum):
    TRADITIONAL_ONLY = "traditional"      # RSA or ECDSA only
    PQ_ONLY = "pq-only"                   # ML-DSA or SLH-DSA only
    HYBRID_COMPOSITE = "hybrid-composite" # Combined PQ+traditional composite cert
    HYBRID_PARALLEL = "hybrid-parallel"   # PQ cert alongside traditional cert


@dataclass
class CertificateInfo:
    subject_cn: str
    key_type: CertKeyType
    key_algorithm: str
    key_bits: int
    is_ca: bool
    is_root: bool
    pq_algorithm: Optional[str] = None
    traditional_algorithm: Optional[str] = None


@dataclass
class HRSResult:
    endpoint: str
    score: int
    max_score: int = 5
    criteria_met: List[str] = field(default_factory=list)
    criteria_missed: List[str] = field(default_factory=list)
    migration_priority: str = ""
    recommendation: str = ""

    def grade(self) -> str:
        if self.score == 5:
            return "A (Fully Hybrid)"
        elif self.score == 4:
            return "B (Near-Hybrid)"
        elif self.score == 3:
            return "C (Partial)"
        elif self.score == 2:
            return "D (Minimal)"
        elif self.score == 1:
            return "E (Emerging)"
        else:
            return "F (Traditional-Only)"


CRITERIA = {
    "HRS-1": "Leaf cert has PQ public key component",
    "HRS-2": "Leaf cert is PQ/T hybrid (both PQ and traditional)",
    "HRS-3": "Intermediate CA(s) are PQ/T hybrid",
    "HRS-4": "Root CA is PQ/T hybrid or PQ-only",
    "HRS-5": "Downgrade protection enforced (HAF/HKF active)",
}

PRIORITY_MAP = {
    (0, 1): "P1-CRITICAL",
    (2, 2): "P2-HIGH",
    (3, 3): "P3-MEDIUM",
    (4, 4): "P4-LOW",
    (5, 5): "P5-COMPLETE",
}


def get_priority(score: int) -> str:
    for (lo, hi), label in PRIORITY_MAP.items():
        if lo <= score <= hi:
            return label
    return "P1-CRITICAL"


def score_endpoint(
    endpoint: str,
    cert_chain: List[CertificateInfo],
    downgrade_protection_active: bool = False,
) -> HRSResult:
    """
    Scores a single MCP server endpoint against the five HRS criteria.
    cert_chain: ordered list from leaf (index 0) to root (last index).
    """
    if not cert_chain:
        return HRSResult(endpoint=endpoint, score=0,
                         criteria_missed=list(CRITERIA.values()),
                         migration_priority="P1-CRITICAL",
                         recommendation="No certificate chain provided.")

    leaf = cert_chain[0]
    intermediates = cert_chain[1:-1]
    root = cert_chain[-1] if len(cert_chain) > 1 else cert_chain[0]

    criteria_met = []
    criteria_missed = []

    # HRS-1: Leaf has any PQ component
    if leaf.key_type in {CertKeyType.PQ_ONLY, CertKeyType.HYBRID_COMPOSITE,
                          CertKeyType.HYBRID_PARALLEL}:
        criteria_met.append("HRS-1")
    else:
        criteria_missed.append("HRS-1")

    # HRS-2: Leaf is PQ/T hybrid
    if leaf.key_type in {CertKeyType.HYBRID_COMPOSITE, CertKeyType.HYBRID_PARALLEL}:
        criteria_met.append("HRS-2")
    else:
        criteria_missed.append("HRS-2")

    # HRS-3: All intermediate CAs are hybrid
    if not intermediates or all(
        c.key_type in {CertKeyType.HYBRID_COMPOSITE, CertKeyType.HYBRID_PARALLEL}
        for c in intermediates
    ):
        criteria_met.append("HRS-3")
    else:
        criteria_missed.append("HRS-3")

    # HRS-4: Root is hybrid or PQ-only
    if root.key_type in {CertKeyType.HYBRID_COMPOSITE, CertKeyType.HYBRID_PARALLEL,
                          CertKeyType.PQ_ONLY}:
        criteria_met.append("HRS-4")
    else:
        criteria_missed.append("HRS-4")

    # HRS-5: Downgrade protection
    if downgrade_protection_active:
        criteria_met.append("HRS-5")
    else:
        criteria_missed.append("HRS-5")

    score = len(criteria_met)
    priority = get_priority(score)

    recommendations = {
        0: "Deploy PQ leaf cert immediately; initiate parallel PKI. Priority: URGENT.",
        1: "Add traditional component to PQ cert for hybrid posture.",
        2: "Extend hybrid certs to intermediate CAs.",
        3: "Migrate root CA to PQ/T hybrid; coordinate with CA provider.",
        4: "Enable HAF/HKF downgrade protection to achieve full HRS-5.",
        5: "Endpoint fully compliant. Maintain hybrid posture through certificate renewals.",
    }

    result = HRSResult(
        endpoint=endpoint,
        score=score,
        criteria_met=criteria_met,
        criteria_missed=criteria_missed,
        migration_priority=priority,
        recommendation=recommendations[score],
    )
    return result


def print_hrs_report(results: List[HRSResult]) -> None:
    print()
    print("  HRS Certificate Inventory Report")
    print(f"  {'Endpoint':<35} {'Score':>6} {'Grade':<20} {'Priority':<15} Recommendation")
    print(f"  {'-'*35} {'-'*6} {'-'*20} {'-'*15} {'-'*40}")
    for r in results:
        print(f"  {r.endpoint:<35} {r.score:>3}/{r.max_score}  {r.grade():<20} "
              f"{r.migration_priority:<15} {r.recommendation[:40]}")


if __name__ == "__main__":
    print("=" * 70)
    print("ContextGuard-MCP-PQC | HRS Calculator Demo")

    # Example inventory
    sample_endpoints = [
        ("mcp-prod-01.internal", [
            CertificateInfo("mcp-prod-01", CertKeyType.TRADITIONAL_ONLY, "ECDSA-P256", 256, False, False),
            CertificateInfo("EnterpriseCA", CertKeyType.TRADITIONAL_ONLY, "RSA-2048", 2048, True, False),
            CertificateInfo("RootCA", CertKeyType.TRADITIONAL_ONLY, "RSA-4096", 4096, True, True),
        ], False),
        ("mcp-staging-01.internal", [
            CertificateInfo("mcp-staging-01", CertKeyType.HYBRID_PARALLEL, "ML-DSA-65+ECDSA-P256", 256, False, False,
                            pq_algorithm="ML-DSA-65", traditional_algorithm="ECDSA-P256"),
            CertificateInfo("EnterpriseCA", CertKeyType.TRADITIONAL_ONLY, "RSA-2048", 2048, True, False),
            CertificateInfo("RootCA", CertKeyType.TRADITIONAL_ONLY, "RSA-4096", 4096, True, True),
        ], True),
        ("mcp-pq-pilot.internal", [
            CertificateInfo("mcp-pq-pilot", CertKeyType.HYBRID_COMPOSITE, "ML-DSA-65+ECDSA-P256", 256, False, False,
                            pq_algorithm="ML-DSA-65", traditional_algorithm="ECDSA-P256"),
            CertificateInfo("HybridIntermCA", CertKeyType.HYBRID_COMPOSITE, "ML-DSA-87+RSA-3072", 3072, True, False,
                            pq_algorithm="ML-DSA-87", traditional_algorithm="RSA-3072"),
            CertificateInfo("HybridRootCA", CertKeyType.HYBRID_COMPOSITE, "ML-DSA-87+RSA-4096", 4096, True, True,
                            pq_algorithm="ML-DSA-87", traditional_algorithm="RSA-4096"),
        ], True),
    ]

    results = []
    for ep, chain, dp in sample_endpoints:
        results.append(score_endpoint(ep, chain, dp))

    print_hrs_report(results)
    print("=" * 70)
