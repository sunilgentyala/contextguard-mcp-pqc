"""
TLS Downgrade Attack Demonstration for MCP Channels
ContextGuard-MCP-PQC | ICSCSA 2026 Paper Artifact

Simulates a cipher suite downgrade attack against an MCP server's TLS
negotiation, showing how an active adversary can force traditional-only
key exchange. Demonstrates ContextGuard HKF enforcement blocking the attack.

RFC 9794 Section 4.2 establishes that hybrid interoperability and hybrid
authentication cannot both be achieved without downgrade protection built
into the protocol negotiation layer. This PoC operationalizes that finding.

Educational use only.
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class HKFMode(Enum):
    DISABLED = "disabled"
    MONITOR = "monitor"
    HYBRID_PREFERRED = "hybrid-preferred"
    HYBRID_REQUIRED = "hybrid-required"


@dataclass
class CipherSuite:
    name: str
    kem_component: str
    signature_component: str
    is_hybrid: bool
    is_pq: bool
    strength_bits: int

    def __str__(self) -> str:
        return self.name


CIPHER_SUITES = {
    # Hybrid PQ+Traditional suites (RFC 9794 compliant)
    "X25519MLKEM768_AES256GCM_SHA384": CipherSuite(
        name="TLS_AES_256_GCM_SHA384 with X25519MLKEM768",
        kem_component="X25519 + ML-KEM-768",
        signature_component="ML-DSA-65",
        is_hybrid=True,
        is_pq=True,
        strength_bits=256,
    ),
    "X25519MLKEM512_AES128GCM_SHA256": CipherSuite(
        name="TLS_AES_128_GCM_SHA256 with X25519MLKEM512",
        kem_component="X25519 + ML-KEM-512",
        signature_component="ECDSA-P256",
        is_hybrid=True,
        is_pq=True,
        strength_bits=128,
    ),
    # Traditional-only suites (quantum-vulnerable)
    "ECDHE_RSA_AES256GCM_SHA384": CipherSuite(
        name="TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
        kem_component="X25519",
        signature_component="RSA-2048",
        is_hybrid=False,
        is_pq=False,
        strength_bits=128,
    ),
    "ECDHE_ECDSA_AES128GCM_SHA256": CipherSuite(
        name="TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
        kem_component="X25519",
        signature_component="ECDSA-P256",
        is_hybrid=False,
        is_pq=False,
        strength_bits=128,
    ),
}


@dataclass
class ClientHello:
    """Simulates a TLS ClientHello with an attacker-controlled cipher suite list."""
    offered_suites: List[str]
    is_adversary_modified: bool = False

    def remove_hybrid_suites(self) -> "ClientHello":
        """Attacker strips hybrid suites from ClientHello before forwarding."""
        traditional_only = [
            s for s in self.offered_suites
            if not CIPHER_SUITES.get(s, CipherSuite("", "", "", False, False, 0)).is_hybrid
        ]
        return ClientHello(
            offered_suites=traditional_only,
            is_adversary_modified=True,
        )


@dataclass
class ServerHelloResult:
    selected_suite_id: str
    downgraded: bool
    hkf_blocked: bool
    hkf_mode: HKFMode
    reason: str


class MCPServerTLSNegotiator:
    """
    Simulates an MCP server's TLS cipher suite selection with ContextGuard HKF.

    In the absence of HKF enforcement, the server selects the highest-priority
    common suite regardless of quantum posture. HKF changes this behavior.
    """

    def __init__(self, hkf_mode: HKFMode = HKFMode.DISABLED):
        self.hkf_mode = hkf_mode
        self.server_supported = list(CIPHER_SUITES.keys())

    def negotiate(self, client_hello: ClientHello) -> ServerHelloResult:
        common = [s for s in client_hello.offered_suites if s in self.server_supported]

        if not common:
            return ServerHelloResult(
                selected_suite_id="NONE",
                downgraded=False,
                hkf_blocked=True,
                hkf_mode=self.hkf_mode,
                reason="No common cipher suites found.",
            )

        # Without HKF, server picks first common suite (attacker wins if hybrid stripped)
        if self.hkf_mode == HKFMode.DISABLED:
            selected_id = common[0]
            suite = CIPHER_SUITES[selected_id]
            downgraded = client_hello.is_adversary_modified and not suite.is_hybrid
            return ServerHelloResult(
                selected_suite_id=selected_id,
                downgraded=downgraded,
                hkf_blocked=False,
                hkf_mode=self.hkf_mode,
                reason="HKF disabled; selected first common suite.",
            )

        # MONITOR: negotiate normally but log if non-hybrid selected
        if self.hkf_mode == HKFMode.MONITOR:
            selected_id = common[0]
            suite = CIPHER_SUITES[selected_id]
            downgraded = not suite.is_hybrid
            return ServerHelloResult(
                selected_suite_id=selected_id,
                downgraded=downgraded,
                hkf_blocked=False,
                hkf_mode=self.hkf_mode,
                reason="HKF monitor: session logged as non-hybrid." if downgraded
                        else "HKF monitor: hybrid suite selected.",
            )

        # HYBRID_PREFERRED: prefer hybrid, fall back with log
        if self.hkf_mode == HKFMode.HYBRID_PREFERRED:
            hybrid_common = [s for s in common if CIPHER_SUITES[s].is_hybrid]
            if hybrid_common:
                selected_id = hybrid_common[0]
                return ServerHelloResult(
                    selected_suite_id=selected_id,
                    downgraded=False,
                    hkf_blocked=False,
                    hkf_mode=self.hkf_mode,
                    reason="HKF preferred: hybrid suite selected.",
                )
            else:
                selected_id = common[0]
                return ServerHelloResult(
                    selected_suite_id=selected_id,
                    downgraded=True,
                    hkf_blocked=False,
                    hkf_mode=self.hkf_mode,
                    reason="HKF preferred: no hybrid suite offered; fallback with warning.",
                )

        # HYBRID_REQUIRED: reject if no hybrid suite available
        if self.hkf_mode == HKFMode.HYBRID_REQUIRED:
            hybrid_common = [s for s in common if CIPHER_SUITES[s].is_hybrid]
            if hybrid_common:
                selected_id = hybrid_common[0]
                return ServerHelloResult(
                    selected_suite_id=selected_id,
                    downgraded=False,
                    hkf_blocked=False,
                    hkf_mode=self.hkf_mode,
                    reason="HKF required: hybrid suite established.",
                )
            else:
                return ServerHelloResult(
                    selected_suite_id="NONE",
                    downgraded=False,
                    hkf_blocked=True,
                    hkf_mode=self.hkf_mode,
                    reason="HKF required: session REJECTED -- no hybrid suite in ClientHello.",
                )

        return ServerHelloResult("NONE", False, False, self.hkf_mode, "Unknown HKF mode.")


def run_downgrade_scenario(hkf_mode: HKFMode, label: str) -> None:
    print(f"\n  Scenario: {label}")
    print(f"  HKF Mode: {hkf_mode.value.upper()}")
    print("  " + "-" * 55)

    # Legitimate client offers hybrid suites first
    legitimate_hello = ClientHello(
        offered_suites=[
            "X25519MLKEM768_AES256GCM_SHA384",
            "X25519MLKEM512_AES128GCM_SHA256",
            "ECDHE_RSA_AES256GCM_SHA384",
            "ECDHE_ECDSA_AES128GCM_SHA256",
        ]
    )

    # Attacker-in-the-middle strips hybrid suites from the forwarded ClientHello
    adversary_modified_hello = legitimate_hello.remove_hybrid_suites()

    server = MCPServerTLSNegotiator(hkf_mode=hkf_mode)

    # What the client intended
    legitimate_result = server.negotiate(legitimate_hello)
    # What the attacker forwards
    attack_result = server.negotiate(adversary_modified_hello)

    suite_legitimate = CIPHER_SUITES.get(legitimate_result.selected_suite_id)
    suite_attack = CIPHER_SUITES.get(attack_result.selected_suite_id)

    print(f"  Client-intended suite:  {legitimate_result.selected_suite_id}")
    if suite_legitimate:
        print(f"    KEM: {suite_legitimate.kem_component} | "
              f"Hybrid: {suite_legitimate.is_hybrid} | PQ: {suite_legitimate.is_pq}")

    print(f"  Attacker-forwarded:     {adversary_modified_hello.offered_suites}")
    print(f"  Server selected:        {attack_result.selected_suite_id}")
    if suite_attack:
        print(f"    KEM: {suite_attack.kem_component} | "
              f"Hybrid: {suite_attack.is_hybrid} | PQ: {suite_attack.is_pq}")

    print(f"  HKF blocked attack:     {attack_result.hkf_blocked}")
    print(f"  Downgrade occurred:     {attack_result.downgraded}")
    print(f"  Outcome: {attack_result.reason}")

    if attack_result.hkf_blocked:
        print("  [PROTECTED] ContextGuard HKF terminated the connection.")
    elif attack_result.downgraded:
        print("  [VULNERABLE] Downgrade to traditional-only succeeded. "
              "Session is HNDL-vulnerable.")
    else:
        print("  [PROTECTED] Hybrid suite negotiated successfully.")


def demonstrate_downgrade_attack() -> None:
    print("=" * 70)
    print("ContextGuard-MCP-PQC | TLS Downgrade Attack Demonstration")
    print("ICSCSA 2026 - Post-Quantum Security for MCP")
    print("=" * 70)
    print()
    print("Attack Model:")
    print("  Adversary intercepts ClientHello and strips X25519MLKEM768")
    print("  cipher suite extensions before forwarding to MCP server.")
    print("  Server, seeing only traditional suites, selects ECDH-only.")
    print("  Result: session is no longer HNDL-resistant.")
    print()
    print("RFC 9794 Section 4.2: Hybrid downgrade protection requires the")
    print("negotiation layer to enforce minimum hybrid posture, not just")
    print("prefer it. This is what ContextGuard HKF implements.")

    for mode, label in [
        (HKFMode.DISABLED, "No HKF (baseline vulnerable MCP server)"),
        (HKFMode.MONITOR, "HKF Monitor (log only, no enforcement)"),
        (HKFMode.HYBRID_PREFERRED, "HKF Hybrid-Preferred (fallback allowed)"),
        (HKFMode.HYBRID_REQUIRED, "HKF Hybrid-Required (full enforcement)"),
    ]:
        run_downgrade_scenario(mode, label)

    print()
    print("=" * 70)
    print("Summary:")
    print("  DISABLED:          Attack succeeds. Traditional-only session established.")
    print("  MONITOR:           Attack succeeds. Event logged but not blocked.")
    print("  HYBRID_PREFERRED:  Attack succeeds with warning. Fallback permitted.")
    print("  HYBRID_REQUIRED:   Attack BLOCKED. Connection refused.")
    print()
    print("Recommended production posture for Tier-1 MCP servers: HYBRID_REQUIRED.")
    print("Phase 2 migration posture: HYBRID_PREFERRED.")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_downgrade_attack()
