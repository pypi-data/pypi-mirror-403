# Frameworks Module

Compliance framework implementations for EU AI Act, SOC2, and HIPAA.

---

## Base Types

### ComplianceRule

::: rotalabs_comply.frameworks.base.ComplianceRule
    options:
      show_bases: false

Definition of a single compliance rule within a framework.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `rule_id` | `str` | Unique identifier within framework |
| `name` | `str` | Human-readable name |
| `description` | `str` | Detailed requirement description |
| `severity` | `RiskLevel` | Default severity for violations |
| `category` | `str` | Category grouping |
| `check_fn` | `Optional[Callable]` | Custom check function |
| `remediation` | `str` | Default remediation guidance |
| `references` | `List[str]` | External references |

**Example:**

```python
from rotalabs_comply.frameworks.base import ComplianceRule, RiskLevel

rule = ComplianceRule(
    rule_id="CUSTOM-001",
    name="Custom Requirement",
    description="Description of what's required",
    severity=RiskLevel.MEDIUM,
    category="custom",
    remediation="How to fix violations",
    references=["Internal Policy 1.2.3"],
)
```

---

### ComplianceFramework Protocol

::: rotalabs_comply.frameworks.base.ComplianceFramework
    options:
      show_bases: false

Protocol defining the interface for compliance frameworks.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Framework name |
| `version` | `str` | Framework version |
| `rules` | `List[ComplianceRule]` | All rules |

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `check` | `async (entry, profile) -> ComplianceCheckResult` | Check entry |
| `get_rule` | `(rule_id: str) -> Optional[ComplianceRule]` | Get rule by ID |
| `list_categories` | `() -> List[str]` | List categories |

---

### BaseFramework

::: rotalabs_comply.frameworks.base.BaseFramework
    options:
      show_bases: false

Abstract base class for compliance frameworks.

### Constructor

```python
BaseFramework(name: str, version: str, rules: List[ComplianceRule])
```

### Abstract Method

Subclasses must implement:

```python
def _check_rule(
    self, entry: AuditEntry, rule: ComplianceRule
) -> Optional[ComplianceViolation]
```

**Example Custom Framework:**

```python
from rotalabs_comply.frameworks.base import BaseFramework, ComplianceRule, RiskLevel

class MyFramework(BaseFramework):
    def __init__(self):
        rules = [
            ComplianceRule(
                rule_id="MY-001",
                name="My Rule",
                description="Description",
                severity=RiskLevel.MEDIUM,
                category="custom",
            ),
        ]
        super().__init__("My Framework", "1.0", rules)

    def _check_rule(self, entry, rule):
        if rule.rule_id == "MY-001":
            if not entry.metadata.get("my_field"):
                return self._create_violation(entry, rule, "my_field missing")
        return None
```

---

### AuditEntry (Frameworks)

::: rotalabs_comply.frameworks.base.AuditEntry
    options:
      show_bases: false

Audit entry structure used by frameworks for compliance checking.

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `entry_id` | `str` | Required | Unique identifier |
| `timestamp` | `datetime` | Required | Event time |
| `event_type` | `str` | Required | Type of event |
| `actor` | `str` | Required | Who triggered event |
| `action` | `str` | Required | Action description |
| `resource` | `str` | `""` | Resource accessed |
| `metadata` | `Dict[str, Any]` | `{}` | Additional context |
| `risk_level` | `RiskLevel` | `LOW` | Risk classification |
| `system_id` | `str` | `""` | AI system identifier |
| `data_classification` | `str` | `"unclassified"` | Data sensitivity |
| `user_notified` | `bool` | `False` | User knows about AI |
| `human_oversight` | `bool` | `False` | Human oversight present |
| `error_handled` | `bool` | `True` | Errors handled gracefully |
| `documentation_ref` | `Optional[str]` | `None` | Documentation reference |

---

### ComplianceProfile (Frameworks)

::: rotalabs_comply.frameworks.base.ComplianceProfile
    options:
      show_bases: false

Configuration profile for compliance evaluation.

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `profile_id` | `str` | Required | Unique identifier |
| `name` | `str` | Required | Profile name |
| `description` | `str` | `""` | Profile description |
| `enabled_frameworks` | `List[str]` | `[]` | Frameworks to evaluate |
| `enabled_categories` | `List[str]` | `[]` | Categories to check |
| `min_severity` | `RiskLevel` | `LOW` | Minimum severity to report |
| `system_classification` | `str` | `"standard"` | System classification |
| `custom_rules` | `List[str]` | `[]` | Additional rule IDs |
| `excluded_rules` | `List[str]` | `[]` | Rules to skip |
| `metadata` | `Dict[str, Any]` | `{}` | Additional config |

---

### ComplianceViolation (Frameworks)

::: rotalabs_comply.frameworks.base.ComplianceViolation
    options:
      show_bases: false

A compliance violation detected during evaluation.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `rule_id` | `str` | Violated rule ID |
| `rule_name` | `str` | Rule name |
| `severity` | `RiskLevel` | Violation severity |
| `description` | `str` | Rule description |
| `evidence` | `str` | Specific evidence |
| `remediation` | `str` | How to fix |
| `entry_id` | `str` | Entry that triggered |
| `category` | `str` | Rule category |
| `framework` | `str` | Framework name |

---

### ComplianceCheckResult (Frameworks)

::: rotalabs_comply.frameworks.base.ComplianceCheckResult
    options:
      show_bases: false

Result of a compliance check against an audit entry.

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `entry_id` | `str` | Checked entry ID |
| `framework` | `str` | Framework name |
| `framework_version` | `str` | Framework version |
| `timestamp` | `datetime` | Check time |
| `violations` | `List[ComplianceViolation]` | Violations found |
| `rules_checked` | `int` | Total rules evaluated |
| `rules_passed` | `int` | Rules that passed |
| `is_compliant` | `bool` | No violations found |
| `metadata` | `Dict[str, Any]` | Additional data |

---

## EU AI Act Framework

::: rotalabs_comply.frameworks.eu_ai_act.EUAIActFramework
    options:
      show_bases: false

EU AI Act (2024) compliance framework.

### Categories

| Category | Description |
|----------|-------------|
| `transparency` | User notification requirements |
| `oversight` | Human oversight requirements |
| `risk_management` | Risk assessment and handling |
| `documentation` | Technical documentation |
| `security` | Cybersecurity measures |

### Rules

| Rule ID | Name | Severity | Category |
|---------|------|----------|----------|
| `EUAI-001` | Human Oversight Documentation | HIGH | oversight |
| `EUAI-002` | AI Interaction Notification | HIGH | transparency |
| `EUAI-003` | Risk Assessment | CRITICAL | risk_management |
| `EUAI-004` | Technical Documentation | HIGH | documentation |
| `EUAI-005` | Data Governance | HIGH | documentation |
| `EUAI-006` | Error Handling | MEDIUM | risk_management |
| `EUAI-007` | Accuracy Monitoring | MEDIUM | risk_management |
| `EUAI-008` | Cybersecurity Measures | HIGH | security |

### Usage

```python
from rotalabs_comply.frameworks.eu_ai_act import EUAIActFramework
from rotalabs_comply.frameworks.base import AuditEntry, ComplianceProfile, RiskLevel
from datetime import datetime

framework = EUAIActFramework()

entry = AuditEntry(
    entry_id="test-001",
    timestamp=datetime.utcnow(),
    event_type="inference",
    actor="user@example.com",
    action="AI response",
    risk_level=RiskLevel.HIGH,
    user_notified=True,
    human_oversight=True,
    metadata={"risk_assessment_documented": True},
)

profile = ComplianceProfile(
    profile_id="eu-ai",
    name="EU AI Compliance",
)

result = await framework.check(entry, profile)
```

### Key Requirements

**High-risk operations require:**
- `human_oversight=True`
- `metadata["risk_assessment_documented"]=True`

**User-facing interactions require:**
- `user_notified=True`

**Inference events require:**
- `metadata["accuracy_monitored"]=True`

---

## SOC2 Framework

::: rotalabs_comply.frameworks.soc2.SOC2Framework
    options:
      show_bases: false

SOC2 Type II compliance framework.

### Categories

| Category | TSC | Description |
|----------|-----|-------------|
| `security` | CC | Common Criteria - Security controls |
| `availability` | A | System availability |
| `processing_integrity` | PI | Data processing accuracy |
| `confidentiality` | C | Confidential information protection |
| `privacy` | P | Personal information protection |

### Rules

| Rule ID | Name | Severity | Category |
|---------|------|----------|----------|
| `SOC2-CC6.1` | Logical Access Controls | HIGH | security |
| `SOC2-CC6.2` | System Boundary Definition | MEDIUM | security |
| `SOC2-CC6.3` | Change Management | MEDIUM | security |
| `SOC2-CC7.1` | System Monitoring | HIGH | security |
| `SOC2-CC7.2` | Incident Response | HIGH | security |
| `SOC2-CC8.1` | Availability Monitoring | MEDIUM | availability |
| `SOC2-A1.1` | Recovery Objectives | MEDIUM | availability |
| `SOC2-PI1.1` | Processing Integrity | MEDIUM | processing_integrity |
| `SOC2-C1.1` | Confidentiality Classification | HIGH | confidentiality |
| `SOC2-P1.1` | Privacy Notice | HIGH | privacy |

### Usage

```python
from rotalabs_comply.frameworks.soc2 import SOC2Framework

framework = SOC2Framework()

entry = AuditEntry(
    entry_id="soc2-001",
    timestamp=datetime.utcnow(),
    event_type="data_access",
    actor="admin@company.com",
    action="Query database",
    data_classification="confidential",
    metadata={
        "access_controlled": True,
        "monitored": True,
    },
)

result = await framework.check(entry, profile)
```

### Key Requirements

**Access events require:**
- Authenticated actor (not "anonymous")
- `metadata["access_controlled"]=True`

**Change events require:**
- `metadata["change_approved"]=True`
- `documentation_ref` set

**Data events require:**
- `data_classification` not "unclassified"

---

## HIPAA Framework

::: rotalabs_comply.frameworks.hipaa.HIPAAFramework
    options:
      show_bases: false

HIPAA compliance framework for PHI handling.

### Categories

| Category | Rule Section | Description |
|----------|--------------|-------------|
| `access_control` | 164.312(a) | System and data access |
| `audit` | 164.312(b) | Audit controls |
| `integrity` | 164.312(c) | Data integrity |
| `authentication` | 164.312(d) | Entity authentication |
| `transmission` | 164.312(e) | Transmission security |
| `privacy` | 164.502/514/530 | Privacy rule |

### Rules

| Rule ID | Name | Severity | Category |
|---------|------|----------|----------|
| `HIPAA-164.312(a)` | Access Control | CRITICAL | access_control |
| `HIPAA-164.312(b)` | Audit Controls | HIGH | audit |
| `HIPAA-164.312(c)` | Integrity Controls | HIGH | integrity |
| `HIPAA-164.312(d)` | Authentication | CRITICAL | authentication |
| `HIPAA-164.312(e)` | Transmission Security | HIGH | transmission |
| `HIPAA-164.502` | Uses and Disclosures | CRITICAL | privacy |
| `HIPAA-164.514` | De-identification | HIGH | privacy |
| `HIPAA-164.530` | Administrative Requirements | MEDIUM | privacy |

### PHI Detection

Rules only apply when `data_classification` contains:

- `"PHI"`
- `"ePHI"`
- `"protected_health_information"`
- `"health_data"`
- `"medical"`
- `"clinical"`

### Usage

```python
from rotalabs_comply.frameworks.hipaa import HIPAAFramework

framework = HIPAAFramework()

# PHI-related entry (rules apply)
entry = AuditEntry(
    entry_id="hipaa-001",
    timestamp=datetime.utcnow(),
    event_type="inference",
    actor="doctor@hospital.com",
    action="AI diagnostic",
    data_classification="PHI",
    metadata={
        "access_controlled": True,
        "encryption_enabled": True,
        "authenticated": True,
        "purpose_documented": True,
        "minimum_necessary_applied": True,
    },
)

result = await framework.check(entry, profile)
```

### Key Requirements

**All PHI access requires:**
- Authenticated actor
- `metadata["access_controlled"]=True`
- `metadata["encryption_enabled"]=True`

**High-risk PHI operations require:**
- `metadata["mfa_verified"]=True`

**PHI use requires:**
- `metadata["purpose_documented"]=True`
- `metadata["minimum_necessary_applied"]=True`
