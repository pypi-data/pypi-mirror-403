# Compliance Checking Tutorial

This tutorial covers using the built-in compliance frameworks (EU AI Act, SOC2, HIPAA) to evaluate AI system operations against regulatory requirements.

## Overview

Compliance checking evaluates audit entries against regulatory frameworks to identify:

- **Violations** -- Specific rules that were not followed
- **Risk levels** -- Severity of identified issues
- **Remediation** -- Steps to fix violations
- **Gaps** -- Areas needing improvement

## Understanding Compliance Frameworks

### Framework Structure

Each framework consists of rules organized by category:

```
Framework (e.g., EU AI Act)
├── Category: Transparency
│   ├── Rule: User Notification (EUAI-002)
│   └── ...
├── Category: Oversight
│   ├── Rule: Human Oversight Documentation (EUAI-001)
│   └── ...
├── Category: Risk Management
│   ├── Rule: Risk Assessment (EUAI-003)
│   └── ...
└── ...
```

### Creating Audit Entries for Compliance

Audit entries need specific fields for compliance checking:

```python
from datetime import datetime
from rotalabs_comply.frameworks.base import AuditEntry, RiskLevel

entry = AuditEntry(
    # Required identifiers
    entry_id="entry-001",
    timestamp=datetime.utcnow(),

    # Event classification
    event_type="inference",       # Type of operation
    actor="user@example.com",     # Who performed it
    action="AI response generation",

    # Resource being accessed
    resource="customer_support_model",
    system_id="prod-ai-001",

    # Risk and data classification
    risk_level=RiskLevel.HIGH,
    data_classification="confidential",

    # Compliance-relevant flags
    user_notified=True,           # Transparency: user knows about AI
    human_oversight=True,         # Oversight: human reviewed
    error_handled=True,           # Robustness: errors handled gracefully
    documentation_ref="DOC-001",  # Documentation: reference to docs

    # Framework-specific metadata
    metadata={
        # EU AI Act
        "risk_assessment_documented": True,
        "accuracy_monitored": True,
        "security_validated": True,
        "data_governance_documented": True,

        # SOC2
        "access_controlled": True,
        "monitored": True,
        "change_approved": True,

        # HIPAA (if PHI involved)
        "encryption_enabled": True,
        "authenticated": True,
        "purpose_documented": True,
        "minimum_necessary_applied": True,
    },
)
```

## EU AI Act Compliance

The EU AI Act (2024) regulates AI systems based on risk level. The framework focuses on high-risk system requirements.

### Rule Categories

| Category | Focus |
|----------|-------|
| `transparency` | User notification of AI interaction |
| `oversight` | Human oversight documentation |
| `risk_management` | Risk assessment, error handling, accuracy |
| `documentation` | Technical and data governance docs |
| `security` | Cybersecurity measures |

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    # Create framework
    framework = EUAIActFramework()

    # List available rules
    print("EU AI Act Rules:")
    for rule in framework.rules:
        print(f"  {rule.rule_id}: {rule.name} [{rule.severity.value}]")

    # Create an audit entry
    entry = AuditEntry(
        entry_id="eu-test-001",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="api-user",
        action="AI chatbot response",
        risk_level=RiskLevel.HIGH,
        user_notified=True,
        human_oversight=True,
        metadata={
            "risk_assessment_documented": True,
            "security_validated": True,
        },
    )

    # Create profile
    profile = ComplianceProfile(
        profile_id="eu-ai-profile",
        name="EU AI Act Compliance",
        enabled_frameworks=["EU AI Act"],
    )

    # Check compliance
    result = await framework.check(entry, profile)

    print(f"\nCompliance Check Result:")
    print(f"  Compliant: {result.is_compliant}")
    print(f"  Rules checked: {result.rules_checked}")
    print(f"  Rules passed: {result.rules_passed}")

    if result.violations:
        print(f"\nViolations ({len(result.violations)}):")
        for v in result.violations:
            print(f"  [{v.severity.value.upper()}] {v.rule_name}")
            print(f"    Evidence: {v.evidence}")

asyncio.run(main())
```

### Key Requirements

**EUAI-001: Human Oversight**
```python
# For high-risk operations, human_oversight must be True
entry = AuditEntry(
    ...,
    risk_level=RiskLevel.HIGH,
    human_oversight=True,  # Required for high-risk
)
```

**EUAI-002: Transparency**
```python
# For user-facing interactions, user must be notified
entry = AuditEntry(
    ...,
    event_type="inference",  # User-facing event
    user_notified=True,      # User knows it's AI
)
```

**EUAI-003: Risk Assessment**
```python
# High-risk operations need documented risk assessment
entry = AuditEntry(
    ...,
    risk_level=RiskLevel.HIGH,
    metadata={"risk_assessment_documented": True},
)
```

## SOC2 Compliance

SOC2 Type II evaluates operational effectiveness of security controls based on AICPA Trust Service Criteria.

### Trust Service Categories

| Category | Code | Focus |
|----------|------|-------|
| Security | CC | Access controls, monitoring, incident response |
| Availability | A | SLA monitoring, recovery objectives |
| Processing Integrity | PI | Input validation, data accuracy |
| Confidentiality | C | Data classification |
| Privacy | P | Privacy notices for personal data |

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.soc2 import SOC2Framework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    framework = SOC2Framework()

    # List categories
    categories = framework.list_categories()
    print(f"SOC2 Categories: {categories}")

    # Create audit entry with SOC2-relevant metadata
    entry = AuditEntry(
        entry_id="soc2-test-001",
        timestamp=datetime.utcnow(),
        event_type="data_access",
        actor="admin@company.com",  # Authenticated user
        action="Query customer database",
        system_id="prod-db-001",
        data_classification="confidential",
        metadata={
            "access_controlled": True,
            "monitored": True,
            "change_approved": True,
        },
    )

    profile = ComplianceProfile(
        profile_id="soc2-profile",
        name="SOC2 Compliance",
        enabled_frameworks=["SOC2 Type II"],
    )

    result = await framework.check(entry, profile)

    print(f"\nSOC2 Check Result:")
    print(f"  Compliant: {result.is_compliant}")
    print(f"  Violations: {len(result.violations)}")

asyncio.run(main())
```

### Key Requirements

**CC6.1: Logical Access Controls**
```python
# All access events need authentication and authorization
entry = AuditEntry(
    ...,
    event_type="data_access",
    actor="user@company.com",  # Must be authenticated (not "anonymous")
    metadata={"access_controlled": True},
)
```

**CC6.3: Change Management**
```python
# Changes need approval and documentation
entry = AuditEntry(
    ...,
    event_type="deployment",
    documentation_ref="CHG-001",  # Change ticket
    metadata={"change_approved": True},
)
```

**C1.1: Confidentiality Classification**
```python
# Data must be classified
entry = AuditEntry(
    ...,
    event_type="data_access",
    data_classification="confidential",  # Not "unclassified"
)
```

## HIPAA Compliance

HIPAA applies to systems processing Protected Health Information (PHI). Rules are only evaluated for PHI-related entries.

### PHI Detection

The framework identifies PHI-related entries by data classification:

```python
# These classifications trigger HIPAA evaluation
phi_classifications = {
    "PHI", "ePHI", "protected_health_information",
    "health_data", "medical", "clinical"
}
```

### Basic Usage

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.hipaa import HIPAAFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    framework = HIPAAFramework()

    # PHI-related entry (HIPAA rules apply)
    phi_entry = AuditEntry(
        entry_id="hipaa-test-001",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="doctor@hospital.com",
        action="AI diagnostic assistance",
        data_classification="PHI",  # Triggers HIPAA
        metadata={
            "access_controlled": True,
            "encryption_enabled": True,
            "authenticated": True,
            "purpose_documented": True,
            "minimum_necessary_applied": True,
        },
    )

    # Non-PHI entry (HIPAA rules don't apply)
    non_phi_entry = AuditEntry(
        entry_id="hipaa-test-002",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="user@company.com",
        action="General AI query",
        data_classification="internal",  # Not PHI
    )

    profile = ComplianceProfile(
        profile_id="hipaa-profile",
        name="HIPAA Compliance",
        enabled_frameworks=["HIPAA"],
    )

    # Check PHI entry
    result1 = await framework.check(phi_entry, profile)
    print(f"PHI Entry - Rules checked: {result1.rules_checked}")

    # Check non-PHI entry
    result2 = await framework.check(non_phi_entry, profile)
    print(f"Non-PHI Entry - Rules checked: {result2.rules_checked}")  # 0

asyncio.run(main())
```

### Key Requirements

**164.312(a): Access Control**
```python
# PHI access requires authentication, authorization, and encryption
entry = AuditEntry(
    ...,
    data_classification="PHI",
    actor="nurse@hospital.com",  # Authenticated
    metadata={
        "access_controlled": True,
        "encryption_enabled": True,
    },
)
```

**164.312(d): Authentication**
```python
# Strong authentication required, MFA for high-risk
entry = AuditEntry(
    ...,
    event_type="bulk_access",  # High-risk operation
    data_classification="PHI",
    metadata={
        "authenticated": True,
        "mfa_verified": True,  # Required for high-risk
    },
)
```

**164.502: Minimum Necessary**
```python
# PHI use must be limited to minimum necessary
entry = AuditEntry(
    ...,
    data_classification="PHI",
    metadata={
        "purpose_documented": True,
        "minimum_necessary_applied": True,
    },
)
```

## Multi-Framework Compliance

Check against multiple frameworks simultaneously:

```python
import asyncio
from datetime import datetime
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.soc2 import SOC2Framework
from rotalabs_comply.frameworks.hipaa import HIPAAFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel

async def main():
    # Initialize all frameworks
    frameworks = {
        "eu_ai_act": EUAIActFramework(),
        "soc2": SOC2Framework(),
        "hipaa": HIPAAFramework(),
    }

    # Create comprehensive entry
    entry = AuditEntry(
        entry_id="multi-test-001",
        timestamp=datetime.utcnow(),
        event_type="inference",
        actor="clinician@hospital.eu",
        action="AI-assisted diagnosis",
        system_id="diag-ai-001",
        risk_level=RiskLevel.HIGH,
        data_classification="PHI",  # HIPAA relevant
        user_notified=True,
        human_oversight=True,
        documentation_ref="DOC-DIAG-001",
        metadata={
            # EU AI Act
            "risk_assessment_documented": True,
            "accuracy_monitored": True,
            "security_validated": True,

            # SOC2
            "access_controlled": True,
            "monitored": True,

            # HIPAA
            "encryption_enabled": True,
            "authenticated": True,
            "purpose_documented": True,
            "minimum_necessary_applied": True,
        },
    )

    profile = ComplianceProfile(
        profile_id="multi-framework",
        name="Multi-Framework Compliance",
        enabled_frameworks=["EU AI Act", "SOC2 Type II", "HIPAA"],
    )

    # Check against all frameworks
    all_violations = []
    for name, framework in frameworks.items():
        result = await framework.check(entry, profile)
        all_violations.extend(result.violations)
        print(f"\n{name}:")
        print(f"  Compliant: {result.is_compliant}")
        print(f"  Violations: {len(result.violations)}")

    # Overall summary
    print(f"\n=== Overall Summary ===")
    print(f"Total violations: {len(all_violations)}")

    # Group by severity
    for severity in ["critical", "high", "medium", "low"]:
        count = sum(
            1 for v in all_violations
            if v.severity.value.lower() == severity
        )
        if count > 0:
            print(f"  {severity.upper()}: {count}")

asyncio.run(main())
```

## Filtering Compliance Checks

### By Category

```python
# Only check security-related rules
profile = ComplianceProfile(
    profile_id="security-only",
    name="Security Focus",
    enabled_categories=["security", "access_control"],
)
```

### By Severity

```python
# Only report medium severity and above
profile = ComplianceProfile(
    profile_id="high-priority",
    name="High Priority Only",
    min_severity=RiskLevel.MEDIUM,
)
```

### Exclude Specific Rules

```python
# Skip specific rules
profile = ComplianceProfile(
    profile_id="customized",
    name="Custom Profile",
    excluded_rules=["EUAI-007", "SOC2-CC8.1"],
)
```

## Handling Violations

### Analyzing Violations

```python
from collections import defaultdict

# Group violations by framework
by_framework = defaultdict(list)
for v in all_violations:
    by_framework[v.framework].append(v)

# Group by severity
by_severity = defaultdict(list)
for v in all_violations:
    by_severity[v.severity.value].append(v)

# Group by category
by_category = defaultdict(list)
for v in all_violations:
    by_category[v.category].append(v)
```

### Remediation Tracking

```python
# Track remediation progress
remediations = {}

for violation in all_violations:
    remediations[violation.rule_id] = {
        "rule_name": violation.rule_name,
        "severity": violation.severity.value,
        "remediation": violation.remediation,
        "status": "pending",
        "assigned_to": None,
        "due_date": None,
    }

# Assign and track
remediations["EUAI-001"]["assigned_to"] = "compliance-team"
remediations["EUAI-001"]["due_date"] = "2026-02-15"
remediations["EUAI-001"]["status"] = "in_progress"
```

## Custom Rule Checks

Add custom validation logic to rules:

```python
from rotalabs_comply.frameworks.base import ComplianceRule, RiskLevel

def check_custom_requirement(entry):
    """Custom check: require specific metadata field."""
    return entry.metadata.get("custom_approval", False)

custom_rule = ComplianceRule(
    rule_id="CUSTOM-001",
    name="Custom Approval Required",
    description="All AI operations require custom approval flag",
    severity=RiskLevel.MEDIUM,
    category="custom",
    check_fn=check_custom_requirement,  # Custom check function
    remediation="Set custom_approval=True in metadata",
)
```

## Best Practices

### 1. Document Everything

```python
# Ensure documentation references exist for significant events
significant_events = ["deployment", "training", "model_update"]
if entry.event_type in significant_events:
    assert entry.documentation_ref, "Documentation required"
```

### 2. Consistent Metadata Schema

```python
# Define required metadata by framework
required_metadata = {
    "eu_ai_act": ["risk_assessment_documented"],
    "soc2": ["access_controlled", "monitored"],
    "hipaa": ["encryption_enabled", "authenticated"],
}

# Validate before logging
def validate_metadata(entry, frameworks):
    for fw in frameworks:
        for field in required_metadata.get(fw, []):
            if field not in entry.metadata:
                raise ValueError(f"Missing {field} for {fw}")
```

### 3. Regular Compliance Scans

```python
async def daily_compliance_scan(logger, frameworks, profile):
    """Run daily compliance scan on recent entries."""
    from datetime import datetime, timedelta

    end = datetime.utcnow()
    start = end - timedelta(days=1)

    entries = await logger.get_entries(start, end)

    all_violations = []
    for entry in entries:
        for fw in frameworks.values():
            result = await fw.check(entry, profile)
            all_violations.extend(result.violations)

    return {
        "entries_checked": len(entries),
        "total_violations": len(all_violations),
        "critical": sum(1 for v in all_violations if v.severity.value == "critical"),
        "high": sum(1 for v in all_violations if v.severity.value == "high"),
    }
```
