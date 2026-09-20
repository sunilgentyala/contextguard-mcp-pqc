"""
Hybrid Authentication Floor (HAF) - ContextGuard-MCP-PQC
Layer 1: Host Authentication and Agent Identity Control

Evaluates MCP host authentication capability at session initiation.
Enforces minimum hybrid signature posture per RFC 9794 PQ/T construct.
Three enforcement tiers:
  - TRADITIONAL_ONLY: classical-only auth detected, logged
  - HYBRID_PREFERRED: hybrid preferred, fallback with warning
  - HYBRID_REQUIRED: session refused if no hybrid auth capability
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class HAFTier(Enum):
    TRADITIONAL_ONLY = "traditional-only"
    HYBRID_PREFERRED = "hybrid-preferred"
    HYBRID_REQUIRED = "hybrid-required"


class AuthMechanism(Enum):
    BEARER_TOKEN_RSA = "bearer+rsa"
    BEARER_TOKEN_ECDSA = "bearer+ecdsa"
    OAUTH2_ECDSA = "oauth2+ecdsa"
    COMPOSITE_HYBRID = "composite-hybrid"      # ML-DSA-65 + ECDSA-P256 composite
    PARALLEL_HYBRID = "parallel-hybrid"        # Separate ML-DSA-65 and ECDSA-P256 chains
    MLONLY_PQ = "ml-dsa-only"                  # PQ-only (no traditional component)


QUANTUM_SAFE_MECHANISMS = {AuthMechanism.COMPOSITE_HYBRID, AuthMechanism.PARALLEL_HYBRID}
HYBRID_MECHANISMS = {AuthMechanism.COMPOSITE_HYBRID, AuthMechanism.PARALLEL_HYBRID}


@dataclass
class AuthCapability:
    mechanism: AuthMechanism
    algorithm_labels: list
    certificate_chain_pq: bool = False
    certificate_chain_hybrid: bool = False


@dataclass
class HAFDecision:
    allowed: bool
    tier_applied: HAFTier
    mechanism: AuthMechanism
    is_hybrid: bool
    log_event: str
    session_classification: str


class HybridAuthFloor:
    """
    Implements HAF policy evaluation per ContextGuard-MCP-PQC framework.

    At MCP server startup, capability is probed. At session initiation,
    the capability is evaluated against the configured HAF tier.
    """

    def __init__(self, tier: HAFTier = HAFTier.HYBRID_PREFERRED):
        self.tier = tier

    def evaluate(self, capability: AuthCapability) -> HAFDecision:
        is_hybrid = capability.mechanism in HYBRID_MECHANISMS
        is_pq_safe = capability.mechanism in QUANTUM_SAFE_MECHANISMS

        if is_hybrid:
            return HAFDecision(
                allowed=True,
                tier_applied=self.tier,
                mechanism=capability.mechanism,
                is_hybrid=True,
                log_event=f"HAF: hybrid auth accepted ({capability.mechanism.value})",
                session_classification="HYBRID_AUTHENTICATED",
            )

        # Traditional-only path
        if self.tier == HAFTier.TRADITIONAL_ONLY:
            return HAFDecision(
                allowed=True,
                tier_applied=self.tier,
                mechanism=capability.mechanism,
                is_hybrid=False,
                log_event=f"HAF: traditional auth ({capability.mechanism.value}); no hybrid enforced",
                session_classification="TRADITIONAL_ONLY",
            )

        if self.tier == HAFTier.HYBRID_PREFERRED:
            return HAFDecision(
                allowed=True,
                tier_applied=self.tier,
                mechanism=capability.mechanism,
                is_hybrid=False,
                log_event=(
                    f"HAF: traditional auth fallback ({capability.mechanism.value}); "
                    "hybrid preferred but not available -- WARNING"
                ),
                session_classification="TRADITIONAL_FALLBACK",
            )

        if self.tier == HAFTier.HYBRID_REQUIRED:
            return HAFDecision(
                allowed=False,
                tier_applied=self.tier,
                mechanism=capability.mechanism,
                is_hybrid=False,
                log_event=(
                    f"HAF: session REJECTED -- hybrid auth required, "
                    f"only {capability.mechanism.value} offered"
                ),
                session_classification="REJECTED",
            )

        return HAFDecision(False, self.tier, capability.mechanism, False, "Unknown tier", "ERROR")
