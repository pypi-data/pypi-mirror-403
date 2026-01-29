"""
Agent Policy Engine (APE) v1.0.1

Deterministic, capability-based policy enforcement runtime for AI agents.

APE provides:
- Explicit intent and plans with cryptographic immutability
- Deterministic runtime state enforcement
- Deterministic policy enforcement
- Capability-based authority via secure tokens
- Enforced authority via AuthorityToken
- Auditable execution
- Integrated escalation handling
- Mandatory schema validation
- Production-grade tooling
- Enforced provenance controls
- Runtime state machine
- Optional multi-tenant isolation

v1.0.1 Additions:
- ActionRepository: Canonical registry of known actions
- IntentCompiler: Transform prompts to structured intents
- PlanGenerator: Generate and validate execution plans
- APEOrchestrator: Unified one-call API from prompt to execution

Two Ways to Use APE:

1. **Orchestrator Path** (Simple)
    from ape import APEOrchestrator
    
    orch = APEOrchestrator.from_policy("policies/read_only.yaml")
    orch.register_tool("read_file", my_read_func)
    result = orch.execute("Read config.json")

2. **Manual Path** (Full Control)
    from ape import (
        PolicyEngine, IntentManager, PlanManager,
        RuntimeOrchestrator, AuthorityManager, EnforcementGate,
        ActionRepository, IntentCompiler, PlanGenerator,
    )
    
    # Wire components yourself for maximum flexibility
    # See IMPLEMENTATION_GUIDE.md for details

Version: 1.0.1
License: Apache-2.0
"""

__version__ = "1.0.1"

# =============================================================================
# Core Errors
# =============================================================================
from ape.errors import (
    # Base error
    APEError,
    
    # Core errors (v1.0)
    IntentError,
    PlanError,
    PlanMutationError,
    ActionError,
    PolicyError,
    PolicyDenyError,
    EscalationRequiredError,
    AuthorityExpiredError,
    UnauthorizedActionError,
    RuntimeStateError,
    ProvenanceError,
    VerificationError,
    SchemaValidationError,
    TokenConsumedError,
    TokenRevokedError,
    TokenNotFoundError,
    TenantMismatchError,
    
    # Action Repository errors (v1.0.1)
    ActionRepositoryError,
    ActionNotFoundError,
    ActionAlreadyExistsError,
    ActionParameterError,
    RepositoryFrozenError,
    
    # Intent Compilation errors (v1.0.1)
    IntentCompilationError,
    IntentNarrowingError,
    IntentAmbiguityError,
    
    # Plan Generation errors (v1.0.1)
    PlanGenerationError,
    PlanValidationError,
    PlanParseError,
    PlanIntentViolationError,
    PlanPolicyViolationError,
    
    # Orchestrator errors (v1.0.1)
    AgentError,
    ToolNotRegisteredError,
    ExecutionError,
)

# =============================================================================
# Configuration
# =============================================================================
from ape.config import (
    RuntimeConfig,
    PolicyConfig,
    EnforcementMode,
    load_config_from_file,
)

# =============================================================================
# Runtime (Core v1.0)
# =============================================================================
from ape.runtime import (
    RuntimeState,
    RuntimeOrchestrator,
    VALID_TRANSITIONS,
    is_valid_transition,
    can_execute,
    can_issue_authority,
)

# =============================================================================
# Provenance (Core v1.0)
# =============================================================================
from ape.provenance import (
    Provenance,
    ProvenanceLabel,
    ProvenanceManager,
    combine_provenance,
)

# =============================================================================
# Action (Core v1.0)
# =============================================================================
from ape.action import Action, validate_action_data

# =============================================================================
# Intent (Core v1.0)
# =============================================================================
from ape.intent import Intent, IntentManager

# =============================================================================
# Plan (Core v1.0)
# =============================================================================
from ape.plan import Plan, PlanStep, PlanManager

# =============================================================================
# Policy (Core v1.0)
# =============================================================================
from ape.policy import (
    Policy,
    PolicyDecision,
    PolicyEngine,
    PolicyEvaluationResult,
    validate_policy_file,
)

# =============================================================================
# Authority (Core v1.0)
# =============================================================================
from ape.authority import AuthorityToken, AuthorityManager

# =============================================================================
# Enforcement (Core v1.0)
# =============================================================================
from ape.enforcement import EnforcementGate, ExecutionResult

# =============================================================================
# Escalation (Core v1.0)
# =============================================================================
from ape.escalation import (
    EscalationHandler,
    EscalationResolver,
    EscalationRequest,
    EscalationResult,
    EscalationDecision,
    DefaultDenyResolver,
)

# =============================================================================
# Audit (Core v1.0)
# =============================================================================
from ape.audit import AuditLogger, AuditEvent, AuditEventType

# =============================================================================
# MCP (Core v1.0)
# =============================================================================
from ape.mcp import MCPScanner, generate_policy_from_mcp

# =============================================================================
# Reference Agent (Core v1.0)
# =============================================================================
from ape.reference_agent import ReferenceAgent, AgentResult, create_simple_agent

# =============================================================================
# Action Repository (v1.0.1)
# =============================================================================
from ape.action_repository import (
    ActionRepository,
    ActionDefinition,
    ActionCategory,
    ActionRiskLevel,
    create_standard_repository,
    get_standard_actions,
)

# =============================================================================
# Intent Compiler (v1.0.1)
# =============================================================================
from ape.intent_compiler import (
    IntentCompiler,
    IntentSignal,
    CompiledIntent,
)

# =============================================================================
# Plan Generator (v1.0.1)
# =============================================================================
from ape.plan_generator import (
    PlanGenerator,
    GeneratedPlanStep,
    GeneratedPlan,
    PlanProposal,
)

# =============================================================================
# Orchestrator (v1.0.1)
# =============================================================================
from ape.orchestrator import (
    APEOrchestrator,
    OrchestrationResult,
)


__all__ = [
    # Version
    "__version__",
    
    # ==========================================================================
    # Errors
    # ==========================================================================
    
    # Base
    "APEError",
    
    # Core errors
    "IntentError",
    "PlanError",
    "PlanMutationError",
    "ActionError",
    "PolicyError",
    "PolicyDenyError",
    "EscalationRequiredError",
    "AuthorityExpiredError",
    "UnauthorizedActionError",
    "RuntimeStateError",
    "ProvenanceError",
    "VerificationError",
    "SchemaValidationError",
    "TokenConsumedError",
    "TokenRevokedError",
    "TokenNotFoundError",
    "TenantMismatchError",
    
    # Action Repository errors (v1.0.1)
    "ActionRepositoryError",
    "ActionNotFoundError",
    "ActionAlreadyExistsError",
    "ActionParameterError",
    "RepositoryFrozenError",
    
    # Intent Compilation errors (v1.0.1)
    "IntentCompilationError",
    "IntentNarrowingError",
    "IntentAmbiguityError",
    
    # Plan Generation errors (v1.0.1)
    "PlanGenerationError",
    "PlanValidationError",
    "PlanParseError",
    "PlanIntentViolationError",
    "PlanPolicyViolationError",
    
    # Orchestrator errors (v1.0.1)
    "AgentError",
    "ToolNotRegisteredError",
    "ExecutionError",
    
    # ==========================================================================
    # Configuration
    # ==========================================================================
    "RuntimeConfig",
    "PolicyConfig",
    "EnforcementMode",
    "load_config_from_file",
    
    # ==========================================================================
    # Core Components (v1.0)
    # ==========================================================================
    
    # Runtime
    "RuntimeState",
    "RuntimeOrchestrator",
    "VALID_TRANSITIONS",
    "is_valid_transition",
    "can_execute",
    "can_issue_authority",
    
    # Provenance
    "Provenance",
    "ProvenanceLabel",
    "ProvenanceManager",
    "combine_provenance",
    
    # Action
    "Action",
    "validate_action_data",
    
    # Intent
    "Intent",
    "IntentManager",
    
    # Plan
    "Plan",
    "PlanStep",
    "PlanManager",
    
    # Policy
    "Policy",
    "PolicyDecision",
    "PolicyEngine",
    "PolicyEvaluationResult",
    "validate_policy_file",
    
    # Authority
    "AuthorityToken",
    "AuthorityManager",
    
    # Enforcement
    "EnforcementGate",
    "ExecutionResult",
    
    # Escalation
    "EscalationHandler",
    "EscalationResolver",
    "EscalationRequest",
    "EscalationResult",
    "EscalationDecision",
    "DefaultDenyResolver",
    
    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    
    # MCP
    "MCPScanner",
    "generate_policy_from_mcp",
    
    # Reference Agent
    "ReferenceAgent",
    "AgentResult",
    "create_simple_agent",
    
    # ==========================================================================
    # v1.0.1 Components
    # ==========================================================================
    
    # Action Repository
    "ActionRepository",
    "ActionDefinition",
    "ActionCategory",
    "ActionRiskLevel",
    "create_standard_repository",
    "get_standard_actions",
    
    # Intent Compiler
    "IntentCompiler",
    "IntentSignal",
    "CompiledIntent",
    
    # Plan Generator
    "PlanGenerator",
    "GeneratedPlanStep",
    "GeneratedPlan",
    "PlanProposal",
    
    # Orchestrator
    "APEOrchestrator",
    "OrchestrationResult",
]
