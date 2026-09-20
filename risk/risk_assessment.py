"""
Quantitative Risk Assessment Engine for MCP Post-Quantum Vulnerabilities
ContextGuard-MCP-PQC | ICSCSA 2026 Paper Artifact

Implements the four-class vulnerability risk scoring described in Section V-C
of the paper. Each class is scored across five dimensions:
  - Exploitability  (E): How easily can an adversary exploit this today?
  - Attack Vector   (AV): Is exploitation local, adjacent, or network-based?
  - CRQC Dependency (Q): Does exploitation require a quantum computer?
  - Sensitivity     (S): How sensitive is the compromised asset?
  - Mitigation Gap  (M): How well does the current spec address this?

Risk score = (E * AV_weight * (1 - Q * crqc_discount) * S * M) / normalization
Range: 0.0 (no risk) to 10.0 (maximum risk)

The CRQC discount reflects that quantum-only attacks have a deferred timeline,
but HNDL attacks begin before CRQC availability, so the discount is partial.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json


# CRQC availability probability by year (expert consensus, Baker et al. 2022 basis)
CRQC_PROBABILITY = {
    2026: 0.01,
    2028: 0.05,
    2030: 0.15,
    2032: 0.30,
    2035: 0.55,
    2038: 0.72,
    2040: 0.85,
}

CURRENT_YEAR = 2026


@dataclass
class VulnerabilityClass:
    """Represents one of the four MCP post-quantum vulnerability classes."""
    name: str
    description: str
    mcp_layer: str
    rfc9794_construct: str

    # Scoring dimensions (1-5 scale each)
    exploitability: float          # 1=hard, 5=trivial
    attack_vector_weight: float    # 1.0=local, 1.5=adjacent, 2.0=network
    crqc_dependency: float         # 0=no CRQC needed, 1=full CRQC required
    sensitivity: float             # 1=low, 5=critical
    mitigation_gap: float          # 1=fully mitigated, 5=no mitigation

    # Qualitative metadata
    affected_assets: List[str] = field(default_factory=list)
    attack_examples: List[str] = field(default_factory=list)
    contextguard_control: str = ""

    def hndl_adjusted_crqc_factor(self) -> float:
        """
        HNDL attacks partially activate CRQC-dependent risks NOW because
        adversaries harvest encrypted traffic today for future decryption.
        Full CRQC dependency score is discounted by 0.4 to reflect HNDL realism.
        """
        hndl_activation = 0.4
        return max(0.0, self.crqc_dependency - hndl_activation)

    def raw_score(self) -> float:
        """Base risk score before normalization."""
        crqc_adjusted = 1.0 - (self.hndl_adjusted_crqc_factor() * 0.3)
        score = (
            self.exploitability
            * self.attack_vector_weight
            * crqc_adjusted
            * self.sensitivity
            * self.mitigation_gap
        )
        return score

    def normalized_score(self) -> float:
        """Risk score normalized to 0-10 range. Max raw score ~= 100."""
        return min(10.0, self.raw_score() / 10.0)

    def risk_level(self) -> str:
        score = self.normalized_score()
        if score >= 8.0:
            return "CRITICAL"
        elif score >= 6.0:
            return "HIGH"
        elif score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mcp_layer": self.mcp_layer,
            "rfc9794_construct": self.rfc9794_construct,
            "exploitability": self.exploitability,
            "attack_vector_weight": self.attack_vector_weight,
            "crqc_dependency": self.crqc_dependency,
            "hndl_adjusted_crqc_factor": round(self.hndl_adjusted_crqc_factor(), 2),
            "sensitivity": self.sensitivity,
            "mitigation_gap": self.mitigation_gap,
            "raw_score": round(self.raw_score(), 2),
            "normalized_score": round(self.normalized_score(), 2),
            "risk_level": self.risk_level(),
            "contextguard_control": self.contextguard_control,
            "affected_assets": self.affected_assets,
        }


def build_vulnerability_classes() -> List[VulnerabilityClass]:
    """
    Defines the four MCP post-quantum vulnerability classes from Section IV.
    Scoring rationale is documented inline.
    """
    return [
        VulnerabilityClass(
            name="V1: Absent Hybrid KEM in Transport",
            description=(
                "MCP specification contains no normative reference to hybrid KEM "
                "design. Transport channels rely on classical TLS 1.3 ECDH key "
                "exchange with no post-quantum component."
            ),
            mcp_layer="Layer 2: Transport Channel",
            rfc9794_construct="PQ/T Composite KEM",
            exploitability=4.0,
            attack_vector_weight=2.0,
            crqc_dependency=0.7,
            sensitivity=5.0,
            mitigation_gap=4.5,
            affected_assets=["Session key material", "Tool invocation payloads"],
            attack_examples=[
                "HNDL harvest of TLS 1.3 MCP sessions",
                "Passive interception of bearer token exchanges",
            ],
            contextguard_control="HKF (Hybrid KEM Floor)",
        ),
        VulnerabilityClass(
            name="V2: Single-Algorithm Server Identity",
            description=(
                "MCP server identity relies exclusively on single-algorithm X.509 "
                "certificates (RSA-2048 or ECDSA-P256). No PQ/T hybrid certificate "
                "or parallel PKI path is specified or deployed."
            ),
            mcp_layer="Layer 3: Server/Tool Identity",
            rfc9794_construct="PQ/T Parallel PKI",
            exploitability=3.5,
            attack_vector_weight=2.0,
            crqc_dependency=0.9,
            sensitivity=4.5,
            mitigation_gap=4.0,
            affected_assets=["Server certificates", "Agent identity tokens"],
            attack_examples=[
                "CRQC-based certificate key recovery",
                "Fraudulent CA issuance after PKI compromise",
            ],
            contextguard_control="HRS (Hybrid Readiness Score)",
        ),
        VulnerabilityClass(
            name="V3: No Hybrid Host Authentication Floor",
            description=(
                "Host authentication uses bearer tokens and OAuth 2.0 flows backed "
                "by quantum-vulnerable RSA/ECDSA signatures. No PQ/T hybrid digital "
                "signature requirement exists in any MCP specification."
            ),
            mcp_layer="Layer 1: Host Authentication",
            rfc9794_construct="PQ/T Hybrid Digital Signature",
            exploitability=3.0,
            attack_vector_weight=2.0,
            crqc_dependency=0.8,
            sensitivity=4.5,
            mitigation_gap=5.0,
            affected_assets=["Agent identity tokens", "OAuth assertions"],
            attack_examples=[
                "CRQC-based signature forgery on OAuth tokens",
                "Agent impersonation via forged identity assertions",
            ],
            contextguard_control="HAF (Hybrid Authentication Floor)",
        ),
        VulnerabilityClass(
            name="V4: Unsigned Tool Results",
            description=(
                "The MCP specification does not require cryptographic signing of "
                "tool results. Most deployed servers return unsigned JSON payloads. "
                "No PQ/T hybrid signature standard exists for result provenance."
            ),
            mcp_layer="Layer 4: Tool Result Integrity",
            rfc9794_construct="PQ/T Hybrid Digital Signature (result)",
            exploitability=3.5,
            attack_vector_weight=1.5,
            crqc_dependency=0.6,
            sensitivity=4.0,
            mitigation_gap=5.0,
            affected_assets=["Tool result contents", "AI agent decision inputs"],
            attack_examples=[
                "Result injection via compromised MCP server",
                "CRQC-assisted result signature forgery",
            ],
            contextguard_control="RSP (Result Signature Policy)",
        ),
    ]


def print_risk_matrix(vulns: List[VulnerabilityClass]) -> None:
    print()
    print("  ContextGuard-MCP-PQC Quantitative Risk Assessment Matrix")
    print(f"  {'Vulnerability':<35} {'Layer':<10} {'E':>4} {'AV':>5} "
          f"{'Q':>4} {'S':>4} {'M':>4} {'Score':>6} {'Level':>10} {'Control'}")
    print(f"  {'-'*35} {'-'*10} {'-'*4} {'-'*5} {'-'*4} {'-'*4} {'-'*4} "
          f"{'-'*6} {'-'*10} {'-'*20}")
    for v in vulns:
        layer_short = v.mcp_layer.split(":")[0].replace("Layer ", "L")
        print(f"  {v.name[:35]:<35} {layer_short:<10} "
              f"{v.exploitability:>4.1f} {v.attack_vector_weight:>5.1f} "
              f"{v.crqc_dependency:>4.1f} {v.sensitivity:>4.1f} "
              f"{v.mitigation_gap:>4.1f} {v.normalized_score():>6.2f} "
              f"{v.risk_level():>10} {v.contextguard_control}")
    print()
    print("  Dimensions: E=Exploitability, AV=Attack Vector Weight,")
    print("  Q=CRQC Dependency (HNDL-adjusted), S=Sensitivity, M=Mitigation Gap")
    print("  Score range: 0.0-10.0 | CRITICAL>=8.0, HIGH>=6.0, MEDIUM>=4.0, LOW<4.0")


def print_priority_queue(vulns: List[VulnerabilityClass]) -> None:
    sorted_vulns = sorted(vulns, key=lambda v: v.normalized_score(), reverse=True)
    print()
    print("  Migration Priority Queue (sorted by risk score):")
    for i, v in enumerate(sorted_vulns, 1):
        print(f"  {i}. [{v.risk_level():<8}] {v.name}")
        print(f"     Score: {v.normalized_score():.2f}/10  |  Control: {v.contextguard_control}")
        print(f"     Assets: {', '.join(v.affected_assets[:2])}")


def save_risk_report(vulns: List[VulnerabilityClass], path: str = "risk_report.json") -> None:
    report = {
        "framework": "ContextGuard-MCP-PQC",
        "paper": "ICSCSA 2026",
        "assessment_year": CURRENT_YEAR,
        "methodology": "CVSS-inspired multi-dimensional scoring with HNDL adjustment",
        "vulnerabilities": [v.to_dict() for v in vulns],
    }
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Risk report saved to: {path}")


def main() -> None:
    print("=" * 70)
    print("ContextGuard-MCP-PQC | Quantitative Risk Assessment")
    print("ICSCSA 2026 - Post-Quantum Security for MCP")
    print("=" * 70)

    vulns = build_vulnerability_classes()
    print_risk_matrix(vulns)
    print_priority_queue(vulns)

    import pathlib
    output_path = pathlib.Path(__file__).parent / "risk_report.json"
    save_risk_report(vulns, str(output_path))

    print()
    print("Key findings:")
    critical = [v for v in vulns if v.risk_level() == "CRITICAL"]
    high = [v for v in vulns if v.risk_level() == "HIGH"]
    print(f"  Critical-risk vulnerabilities: {len(critical)}")
    print(f"  High-risk vulnerabilities:     {len(high)}")
    print()
    print("  All four vulnerability classes score HIGH or above due to:")
    print("  1. HNDL activation (harvest begins without CRQC, deferred decrypt)")
    print("  2. Complete absence of mitigation in published MCP specifications")
    print("  3. Network-facing attack vectors on production AI infrastructure")
    print("=" * 70)


if __name__ == "__main__":
    main()
