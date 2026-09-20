"""
HNDL (Harvest-Now-Decrypt-Later) Demonstration for MCP Sessions
ContextGuard-MCP-PQC | ICSCSA 2026 Paper Artifact

This script simulates the HNDL threat against MCP TLS sessions that use
traditional RSA/ECDH key exchange. It shows what an adversary captures
today, the estimated timeline to decryption, and how ContextGuard-MCP-PQC
mitigates the threat via RFC 9794 hybrid KEM enforcement.

Educational use only. No real network traffic is intercepted.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CapturedSession:
    """Represents an MCP TLS session as captured by a passive HNDL adversary."""
    session_id: str
    capture_timestamp: str
    tls_version: str
    cipher_suite: str
    server_cert_alg: str
    server_cert_key_bits: int
    client_hello_random: bytes
    server_hello_random: bytes
    encrypted_premaster: Optional[bytes]        # RSA path
    ecdh_ephemeral_pubkey: Optional[bytes]      # ECDH path
    encrypted_payload_bytes: int
    estimated_payload_sensitivity: str
    mcp_tool_name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "capture_timestamp": self.capture_timestamp,
            "tls_version": self.tls_version,
            "cipher_suite": self.cipher_suite,
            "server_cert_alg": self.server_cert_alg,
            "server_cert_key_bits": self.server_cert_key_bits,
            "encrypted_payload_bytes": self.encrypted_payload_bytes,
            "estimated_payload_sensitivity": self.estimated_payload_sensitivity,
            "mcp_tool_name": self.mcp_tool_name,
            "quantum_vulnerable": True,
        }


@dataclass
class QuantumDecryptionTimeline:
    """
    Projects when a captured session could be decrypted given quantum progress.

    Numbers derived from: Banegas et al. (2023) and updated estimates from
    Webber et al. (2022) on fault-tolerant quantum computation timelines.
    Physical qubit estimates updated per February 2026 analysis reducing
    RSA-2048 factoring threshold below 100,000 physical qubits.
    """
    key_algorithm: str
    key_bits: int
    current_year: int = 2026
    optimistic_crqc_year: int = 2030
    consensus_crqc_year: int = 2035
    conservative_crqc_year: int = 2040

    def years_to_decryption_optimistic(self) -> int:
        return self.optimistic_crqc_year - self.current_year

    def years_to_decryption_consensus(self) -> int:
        return self.consensus_crqc_year - self.current_year

    def sensitivity_still_valid(self, sensitivity_horizon_years: int) -> bool:
        """
        Returns True if the session's intelligence value outlasts the optimistic
        CRQC timeline -- i.e., the HNDL threat is operationally relevant.
        """
        return sensitivity_horizon_years >= self.years_to_decryption_optimistic()


def simulate_mcp_session_capture(
    cipher_suite: str = "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
    mcp_tool: str = "database_query",
    payload_bytes: int = 4096,
) -> CapturedSession:
    """Simulates passive capture of an MCP TLS session."""
    now = datetime.now(timezone.utc).isoformat()
    rng = os.urandom
    session = CapturedSession(
        session_id=hashlib.sha256(rng(32)).hexdigest()[:16],
        capture_timestamp=now,
        tls_version="TLS 1.3",
        cipher_suite=cipher_suite,
        server_cert_alg="ECDSA-P256",
        server_cert_key_bits=256,
        client_hello_random=rng(32),
        server_hello_random=rng(32),
        encrypted_premaster=None,
        ecdh_ephemeral_pubkey=rng(65),
        encrypted_payload_bytes=payload_bytes,
        estimated_payload_sensitivity="HIGH",
        mcp_tool_name=mcp_tool,
    )
    return session


def assess_hndl_risk(session: CapturedSession) -> dict:
    """
    Evaluates the HNDL risk for a captured session.

    Sensitivity horizons (years) are taken from Table I of the paper:
      - Agent identity tokens:  3-5 years
      - Session key material:   10-15 years
      - Tool invocation payloads: 5-10 years
    """
    SENSITIVITY_HORIZONS = {
        "agent_identity": 5,
        "session_key": 12,
        "tool_payload": 7,
        "tool_result": 5,
        "server_certificate": 7,
        "pki_root": 25,
    }

    timeline = QuantumDecryptionTimeline(
        key_algorithm=session.server_cert_alg,
        key_bits=session.server_cert_key_bits,
    )

    risks = {}
    for asset, horizon in SENSITIVITY_HORIZONS.items():
        risks[asset] = {
            "horizon_years": horizon,
            "optimistic_threat_years": timeline.years_to_decryption_optimistic(),
            "consensus_threat_years": timeline.years_to_decryption_consensus(),
            "hndl_relevant": timeline.sensitivity_still_valid(horizon),
            "risk_level": (
                "CRITICAL" if horizon >= 10
                else "HIGH" if horizon >= 5
                else "MEDIUM"
            ),
        }
    return risks


def demonstrate_hndl_scenario() -> None:
    print("=" * 70)
    print("ContextGuard-MCP-PQC | HNDL Threat Demonstration")
    print("ICSCSA 2026 - Post-Quantum Security for MCP")
    print("=" * 70)
    print()

    # Phase 1: Simulate capture
    print("[PHASE 1] Passive Harvest: MCP Session Capture")
    print("-" * 50)
    mcp_tools = [
        ("database_query", 8192),
        ("auth_token_refresh", 512),
        ("file_retrieval", 32768),
    ]

    captured_sessions = []
    for tool_name, size in mcp_tools:
        session = simulate_mcp_session_capture(
            mcp_tool=tool_name,
            payload_bytes=size,
        )
        captured_sessions.append(session)
        print(f"  Captured: {session.session_id} | Tool: {tool_name} | "
              f"{size} bytes | {session.cipher_suite}")
    print(f"\n  Total sessions in HNDL archive: {len(captured_sessions)}")
    print(f"  All sessions use quantum-vulnerable ECDH key exchange.")
    print(f"  Session key material recoverable once CRQC is available.\n")

    # Phase 2: Risk assessment
    print("[PHASE 2] Risk Assessment: Decryption Timeline")
    print("-" * 50)
    timeline = QuantumDecryptionTimeline(
        key_algorithm="ECDSA-P256",
        key_bits=256,
    )
    print(f"  Adversary CRQC timeline estimates (current year: {timeline.current_year}):")
    print(f"    Optimistic:    {timeline.optimistic_crqc_year} "
          f"({timeline.years_to_decryption_optimistic()} years)")
    print(f"    Consensus:     {timeline.consensus_crqc_year} "
          f"({timeline.years_to_decryption_consensus()} years)")
    print(f"    Conservative:  {timeline.conservative_crqc_year}\n")

    risks = assess_hndl_risk(captured_sessions[0])
    print("  Asset-level HNDL risk (MCP session):")
    print(f"  {'Asset':<25} {'Horizon':>8} {'Opt.Threat':>12} {'HNDL Relevant':>15} {'Risk':>10}")
    print(f"  {'-'*25} {'-'*8} {'-'*12} {'-'*15} {'-'*10}")
    for asset, r in risks.items():
        relevant_str = "YES" if r["hndl_relevant"] else "no"
        print(f"  {asset:<25} {r['horizon_years']:>6}yr "
              f"  {r['optimistic_threat_years']:>6}yr "
              f"  {relevant_str:>13}  {r['risk_level']:>10}")

    # Phase 3: ContextGuard mitigation
    print()
    print("[PHASE 3] ContextGuard-MCP-PQC Mitigation")
    print("-" * 50)
    print("  HKF (Hybrid KEM Floor) enforcement: ENABLED")
    print("  Minimum cipher suite: X25519MLKEM768")
    print()
    protected_cipher = "TLS_AES_256_GCM_SHA384 + X25519MLKEM768"
    print(f"  Hybrid session established: {protected_cipher}")
    print("  Key exchange security:")
    print("    X25519:      Classical confidentiality (present-threat)")
    print("    ML-KEM-768:  Post-quantum confidentiality (future-threat)")
    print("    Combined:    HNDL adversary must break BOTH components")
    print()
    print("  Result: Captured ciphertext is computationally infeasible to")
    print("  decrypt even with a CRQC, because ML-KEM-768 provides IND-CCA2")
    print("  security against quantum adversaries (NIST FIPS 203, Aug 2024).")
    print()
    print("[CONCLUSION] Sessions protected by ContextGuard HKF are resistant")
    print("to HNDL attacks. Traditional-only sessions in the archive remain")
    print("vulnerable once a CRQC becomes available.")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_hndl_scenario()
