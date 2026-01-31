"""
Compliance frameworks for AI system evaluation.

This module provides implementations of major compliance frameworks
for evaluating AI system behavior against regulatory requirements:

- EU AI Act: European Union's comprehensive AI regulation
- SOC2 Type II: AICPA Trust Service Criteria for service organizations
- HIPAA: US healthcare data protection requirements

Each framework implements the ComplianceFramework protocol and can be
used to check audit entries for compliance violations.

Example:
    >>> from rotalabs_comply.frameworks import EUAIActFramework, SOC2Framework
    >>> from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile
    >>>
    >>> # Create a framework instance
    >>> eu_ai = EUAIActFramework()
    >>>
    >>> # Create an audit entry to check
    >>> entry = AuditEntry(
    ...     entry_id="test-001",
    ...     timestamp=datetime.utcnow(),
    ...     event_type="inference",
    ...     actor="user@example.com",
    ...     action="Generated text response",
    ... )
    >>>
    >>> # Create a compliance profile
    >>> profile = ComplianceProfile(
    ...     profile_id="default",
    ...     name="Default Profile",
    ... )
    >>>
    >>> # Check compliance
    >>> result = await eu_ai.check(entry, profile)
    >>> print(f"Compliant: {result.is_compliant}")
"""

from .base import (
    AuditEntry,
    BaseFramework,
    ComplianceCheckResult,
    ComplianceFramework,
    ComplianceProfile,
    ComplianceRule,
    ComplianceViolation,
    RiskLevel,
)
from .eu_ai_act import EUAIActFramework
from .hipaa import HIPAAFramework
from .soc2 import SOC2Framework

__all__ = [
    # Base types
    "RiskLevel",
    "AuditEntry",
    "ComplianceProfile",
    "ComplianceViolation",
    "ComplianceCheckResult",
    "ComplianceRule",
    "ComplianceFramework",
    "BaseFramework",
    # Frameworks
    "EUAIActFramework",
    "SOC2Framework",
    "HIPAAFramework",
]
