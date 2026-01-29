"""
APE Command Line Interface v1.0.1

Per architecture spec (§14 CLI):
- Policy validation
- Policy simulation
- Prompt testing (v1.0.1)
- Intent analysis (v1.0.1)
- Action repository inspection (v1.0.1)
- Attack test execution
- Audit inspection
- Verification export

CLI guarantees:
- Deterministic exit codes
- Typed error output
- Read-only safety (no authority issuance)

Exit codes:
- 0: Success
- 1: General error
- 2: Policy error
- 3: Validation error
- 4: File not found
- 5: Intent compilation error (v1.0.1)
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from ape.policy.engine import PolicyEngine, PolicyDecision, validate_policy_file
from ape.errors import (
    PolicyError, 
    PolicyDenyError, 
    EscalationRequiredError,
    IntentCompilationError,
    IntentAmbiguityError,
    IntentNarrowingError,
)
from ape.mcp.scanner import MCPScanner, generate_policy_from_mcp
from ape.action_repository import (
    ActionRepository,
    ActionDefinition,
    ActionCategory,
    ActionRiskLevel,
    create_standard_repository,
)
from ape.intent_compiler import IntentCompiler, CompiledIntent
from ape.plan_generator import PlanGenerator


# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_POLICY_ERROR = 2
EXIT_VALIDATION_ERROR = 3
EXIT_FILE_NOT_FOUND = 4
EXIT_INTENT_ERROR = 5


# =============================================================================
# Policy Commands (v1.0)
# =============================================================================

def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a policy file."""
    policy_path = Path(args.policy)
    if not policy_path.exists():
        print(f"FILE_NOT_FOUND: {args.policy}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    
    errors = validate_policy_file(args.policy)
    
    if errors:
        print(f"VALIDATION FAILED: {args.policy}", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    
    print(f"✓ VALID: {args.policy}")
    return EXIT_SUCCESS


def cmd_simulate(args: argparse.Namespace) -> int:
    """Simulate policy evaluation for an action."""
    try:
        engine = PolicyEngine(args.policy)
        result = engine.evaluate(args.action)
        
        if args.json:
            output = {
                "action": args.action,
                "decision": result.decision.value,
                "reason": result.reason,
            }
            print(json.dumps(output, indent=2))
        else:
            status = "✓" if result.is_allowed() else "✗" if result.is_denied() else "⚠"
            print(f"{status} {args.action}: {result.decision.value}")
            if args.verbose:
                print(f"  Reason: {result.reason}")
        
        if result.decision == PolicyDecision.ALLOW:
            return EXIT_SUCCESS
        elif result.decision == PolicyDecision.ESCALATE:
            return EXIT_SUCCESS  # Escalate is not an error
        else:
            return EXIT_POLICY_ERROR
            
    except FileNotFoundError:
        print(f"FILE_NOT_FOUND: {args.policy}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    except PolicyError as e:
        print(f"POLICY_ERROR: {e}", file=sys.stderr)
        return EXIT_POLICY_ERROR


def cmd_simulate_batch(args: argparse.Namespace) -> int:
    """Simulate policy evaluation for multiple actions."""
    try:
        engine = PolicyEngine(args.policy)
        
        # Read actions from file or args
        if args.actions_file:
            with open(args.actions_file) as f:
                actions = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            actions = args.actions
        
        if not actions:
            print("ERROR: No actions specified", file=sys.stderr)
            return EXIT_ERROR
        
        results = engine.simulate(actions)
        
        if args.json:
            output = [
                {
                    "action": r.action_id,
                    "decision": r.decision.value,
                    "reason": r.reason
                }
                for r in results
            ]
            print(json.dumps(output, indent=2))
        else:
            allowed = 0
            denied = 0
            escalate = 0
            
            for result in results:
                status = "✓" if result.is_allowed() else "✗" if result.is_denied() else "⚠"
                print(f"{status} {result.action_id}: {result.decision.value}")
                
                if result.is_allowed():
                    allowed += 1
                elif result.is_denied():
                    denied += 1
                else:
                    escalate += 1
            
            print(f"\nSummary: {allowed} allowed, {denied} denied, {escalate} escalate")
        
        return EXIT_SUCCESS
        
    except FileNotFoundError as e:
        print(f"FILE_NOT_FOUND: {e}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    except PolicyError as e:
        print(f"POLICY_ERROR: {e}", file=sys.stderr)
        return EXIT_POLICY_ERROR


def cmd_info(args: argparse.Namespace) -> int:
    """Show information about a policy."""
    try:
        engine = PolicyEngine(args.policy)
        policy = engine.policy
        
        if args.json:
            output = {
                "version": engine.version,
                "name": policy.name,
                "description": policy.description,
                "allowed_actions": policy.allowed_actions,
                "forbidden_actions": policy.forbidden_actions,
                "escalation_required": policy.escalation_required,
                "default_deny": policy.default_deny,
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Policy: {args.policy}")
            print(f"Version: {engine.version[:16]}...")
            if policy.name:
                print(f"Name: {policy.name}")
            if policy.description:
                print(f"Description: {policy.description}")
            print(f"Default Deny: {policy.default_deny}")
            print(f"\nAllowed Actions ({len(policy.allowed_actions)}):")
            for action in sorted(policy.allowed_actions):
                print(f"  ✓ {action}")
            if policy.forbidden_actions:
                print(f"\nForbidden Actions ({len(policy.forbidden_actions)}):")
                for action in sorted(policy.forbidden_actions):
                    print(f"  ✗ {action}")
            if policy.escalation_required:
                print(f"\nEscalation Required ({len(policy.escalation_required)}):")
                for action in sorted(policy.escalation_required):
                    print(f"  ⚠ {action}")
        
        return EXIT_SUCCESS
        
    except FileNotFoundError:
        print(f"FILE_NOT_FOUND: {args.policy}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    except PolicyError as e:
        print(f"POLICY_ERROR: {e}", file=sys.stderr)
        return EXIT_POLICY_ERROR


def cmd_diff(args: argparse.Namespace) -> int:
    """Compare two policy files."""
    try:
        engine1 = PolicyEngine(args.policy1)
        engine2 = PolicyEngine(args.policy2)
        
        policy1 = engine1.policy
        policy2 = engine2.policy
        
        set1_allow = set(policy1.allowed_actions)
        set2_allow = set(policy2.allowed_actions)
        set1_deny = set(policy1.forbidden_actions)
        set2_deny = set(policy2.forbidden_actions)
        set1_escalate = set(policy1.escalation_required)
        set2_escalate = set(policy2.escalation_required)
        
        # Find differences
        only_in_1_allow = set1_allow - set2_allow
        only_in_2_allow = set2_allow - set1_allow
        both_allow = set1_allow & set2_allow
        
        # Actions that changed decision
        changed = []
        all_actions = set1_allow | set2_allow | set1_deny | set2_deny | set1_escalate | set2_escalate
        
        for action in all_actions:
            decision1 = "allow" if action in set1_allow else "deny" if action in set1_deny else "escalate" if action in set1_escalate else "default"
            decision2 = "allow" if action in set2_allow else "deny" if action in set2_deny else "escalate" if action in set2_escalate else "default"
            if decision1 != decision2:
                changed.append((action, decision1, decision2))
        
        if args.json:
            output = {
                "policy1": args.policy1,
                "policy2": args.policy2,
                "same_allow": sorted(both_allow),
                "only_in_policy1": sorted(only_in_1_allow),
                "only_in_policy2": sorted(only_in_2_allow),
                "changed": [{"action": a, "from": f, "to": t} for a, f, t in changed],
            }
            print(json.dumps(output, indent=2))
        else:
            name1 = policy1.name or Path(args.policy1).stem
            name2 = policy2.name or Path(args.policy2).stem
            
            print(f"Policy Comparison")
            print(f"=================")
            print(f"Policy 1: {name1} ({args.policy1})")
            print(f"Policy 2: {name2} ({args.policy2})")
            
            if both_allow:
                print(f"\nSame in both ({len(both_allow)}):")
                for action in sorted(both_allow):
                    print(f"  {action}: allow")
            
            if changed:
                print(f"\nChanged ({len(changed)}):")
                for action, from_decision, to_decision in sorted(changed):
                    print(f"  {action}: {from_decision} → {to_decision}")
            
            if only_in_1_allow:
                print(f"\nOnly allowed in {name1} ({len(only_in_1_allow)}):")
                for action in sorted(only_in_1_allow):
                    print(f"  + {action}")
            
            if only_in_2_allow:
                print(f"\nOnly allowed in {name2} ({len(only_in_2_allow)}):")
                for action in sorted(only_in_2_allow):
                    print(f"  + {action}")
            
            # Risk assessment
            if len(set2_allow) > len(set1_allow):
                print(f"\n⚠ {name2} is MORE PERMISSIVE than {name1}")
            elif len(set2_allow) < len(set1_allow):
                print(f"\n✓ {name2} is MORE RESTRICTIVE than {name1}")
            else:
                print(f"\n≈ Policies have similar permission levels")
        
        return EXIT_SUCCESS
        
    except FileNotFoundError as e:
        print(f"FILE_NOT_FOUND: {e}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    except PolicyError as e:
        print(f"POLICY_ERROR: {e}", file=sys.stderr)
        return EXIT_POLICY_ERROR


# =============================================================================
# MCP Commands (v1.0)
# =============================================================================

def cmd_mcp_scan(args: argparse.Namespace) -> int:
    """Scan MCP configuration and generate a policy."""
    try:
        policy_data = generate_policy_from_mcp(
            args.mcp_config,
            policy_name=args.name,
            default_deny=not args.allow_unlisted
        )
        
        if args.output:
            import yaml
            with open(args.output, 'w') as f:
                yaml.dump(policy_data, f, default_flow_style=False, sort_keys=False)
            print(f"✓ Policy written to: {args.output}")
        else:
            import yaml
            print(yaml.dump(policy_data, default_flow_style=False, sort_keys=False))
        
        return EXIT_SUCCESS
        
    except FileNotFoundError as e:
        print(f"FILE_NOT_FOUND: {e}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR


def cmd_mcp_info(args: argparse.Namespace) -> int:
    """Show information about an MCP configuration."""
    try:
        scanner = MCPScanner(args.mcp_config)
        tools = scanner.get_all_tools()
        
        if args.json:
            print(json.dumps(tools, indent=2))
        else:
            print(f"MCP Configuration: {args.mcp_config}")
            print(f"Servers: {len(scanner.get_servers())}")
            print(f"Total Tools: {len(tools)}")
            print("\nTools by server:")
            for server_name, server_tools in scanner.get_tools_by_server().items():
                print(f"\n  {server_name} ({len(server_tools)} tools):")
                for tool in sorted(server_tools):
                    print(f"    - {tool}")
        
        return EXIT_SUCCESS
        
    except FileNotFoundError as e:
        print(f"FILE_NOT_FOUND: {e}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR


# =============================================================================
# v1.0.1 Commands - Intent & Prompt Testing
# =============================================================================

def cmd_test_prompt(args: argparse.Namespace) -> int:
    """Test a prompt against a policy through the full intent compilation pipeline."""
    try:
        # Load policy
        policy = PolicyEngine(args.policy)
        policy_allowed = policy.get_all_allowed_actions()
        policy_forbidden = policy.get_all_forbidden_actions()
        
        # Load repository
        if args.repository:
            repository = ActionRepository.load(args.repository)
        else:
            repository = create_standard_repository()
        
        # Create compiler
        compiler = IntentCompiler(repository)
        
        # Parse risk level
        risk_level = ActionRiskLevel.MODERATE
        if args.max_risk:
            try:
                risk_level = ActionRiskLevel(args.max_risk.upper())
            except ValueError:
                print(f"ERROR: Invalid risk level '{args.max_risk}'. Use: minimal, low, moderate, high, critical", file=sys.stderr)
                return EXIT_ERROR
        
        # Compile intent
        try:
            intent = compiler.compile(
                prompt=args.prompt,
                policy_allowed=policy_allowed,
                policy_forbidden=policy_forbidden,
                max_risk_level=risk_level,
            )
        except IntentAmbiguityError as e:
            if args.json:
                print(json.dumps({"error": "ambiguous", "message": str(e)}))
            else:
                print(f"✗ AMBIGUOUS: Could not understand prompt")
                print(f"  {e}")
            return EXIT_INTENT_ERROR
        except IntentNarrowingError as e:
            if args.json:
                print(json.dumps({"error": "narrowing", "message": str(e)}))
            else:
                print(f"✗ BLOCKED: No actions allowed by policy")
                print(f"  {e}")
            return EXIT_INTENT_ERROR
        
        if args.json:
            output = {
                "prompt": args.prompt,
                "success": True,
                "intent": {
                    "allowed_actions": intent.allowed_actions,
                    "forbidden_actions": intent.forbidden_actions,
                    "escalation_required": intent.escalation_required,
                    "scope": intent.scope,
                    "confidence": intent.confidence,
                },
                "signals": [
                    {
                        "phrase": s.phrase,
                        "actions": s.action_ids,
                        "confidence": s.confidence,
                    }
                    for s in intent.signals
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Prompt: \"{args.prompt}\"")
            print(f"Policy: {args.policy}")
            print()
            
            # Show extracted signals
            if intent.signals:
                print("Signals Extracted:")
                for signal in intent.signals:
                    print(f"  \"{signal.phrase}\" → {signal.action_ids} (confidence: {signal.confidence:.2f})")
                print()
            
            # Show intent results
            print("Compiled Intent:")
            if intent.allowed_actions:
                print(f"  Allowed ({len(intent.allowed_actions)}):")
                for action in intent.allowed_actions:
                    print(f"    ✓ {action}")
            else:
                print("  Allowed: (none)")
            
            if intent.escalation_required:
                print(f"  Escalation Required ({len(intent.escalation_required)}):")
                for action in intent.escalation_required:
                    print(f"    ⚠ {action}")
            
            if intent.forbidden_actions:
                print(f"  Forbidden ({len(intent.forbidden_actions)}):")
                for action in intent.forbidden_actions:
                    print(f"    ✗ {action}")
            
            print()
            print(f"Scope: {intent.scope}")
            print(f"Confidence: {intent.confidence:.2f}")
            
            # Summary
            print()
            if intent.allowed_actions:
                print(f"✓ PASS: Intent compiles with {len(intent.allowed_actions)} allowed action(s)")
            else:
                print(f"✗ FAIL: No actions would be allowed")
        
        return EXIT_SUCCESS if intent.allowed_actions else EXIT_INTENT_ERROR
        
    except FileNotFoundError as e:
        print(f"FILE_NOT_FOUND: {e}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    except IntentCompilationError as e:
        print(f"INTENT_ERROR: {e}", file=sys.stderr)
        return EXIT_INTENT_ERROR
    except PolicyError as e:
        print(f"POLICY_ERROR: {e}", file=sys.stderr)
        return EXIT_POLICY_ERROR


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze a prompt to see what signals and actions would be extracted."""
    try:
        # Load repository
        if args.repository:
            repository = ActionRepository.load(args.repository)
        else:
            repository = create_standard_repository()
        
        # Create compiler
        compiler = IntentCompiler(repository)
        
        # Analyze prompt
        analysis = compiler.analyze(args.prompt)
        
        if args.json:
            # Convert any non-serializable objects
            output = {
                "prompt": args.prompt,
                "signals_extracted": [
                    {
                        "phrase": s.phrase,
                        "action_ids": s.action_ids,
                        "confidence": s.confidence,
                        "category": s.category.value if s.category else None,
                    }
                    for s in analysis.get("signals_extracted", [])
                ],
                "candidate_actions": analysis.get("candidate_actions", []),
                "scope_hint": analysis.get("scope_hint"),
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Prompt Analysis")
            print(f"===============")
            print(f"Prompt: \"{args.prompt}\"")
            print()
            
            signals = analysis.get("signals_extracted", [])
            if signals:
                print(f"Signals Extracted ({len(signals)}):")
                for signal in signals:
                    category = f" [{signal.category.value}]" if signal.category else ""
                    print(f"  • \"{signal.phrase}\"{category}")
                    for action_id in signal.action_ids:
                        print(f"      → {action_id} (confidence: {signal.confidence:.2f})")
            else:
                print("No signals extracted")
                print("  The prompt doesn't match any known action patterns.")
                print("  Try using more specific action words like 'read', 'write', 'list', 'delete', etc.")
            
            candidates = analysis.get("candidate_actions", [])
            if candidates:
                print(f"\nCandidate Actions ({len(candidates)}):")
                for candidate in candidates:
                    print(f"  • {candidate['action_id']} (confidence: {candidate['confidence']:.2f})")
            
            scope = analysis.get("scope_hint")
            if scope:
                print(f"\nScope Hint: {scope}")
        
        return EXIT_SUCCESS
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR


def cmd_actions(args: argparse.Namespace) -> int:
    """List actions in the Action Repository."""
    try:
        # Load repository
        if args.repository:
            repository = ActionRepository.load(args.repository)
        else:
            repository = create_standard_repository()
        
        if args.json:
            output = {
                "count": repository.count,
                "actions": [
                    {
                        "action_id": defn.action_id,
                        "description": defn.description,
                        "category": defn.category.value,
                        "risk_level": defn.risk_level.value,
                        "requires_human_review": defn.requires_human_review,
                        "tags": defn.tags,
                    }
                    for defn in repository.all_actions
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Action Repository ({repository.count} actions)")
            print("=" * 50)
            
            # Group by category if requested
            if args.by_category:
                by_category: dict[ActionCategory, list[ActionDefinition]] = {}
                for defn in repository.all_actions:
                    if defn.category not in by_category:
                        by_category[defn.category] = []
                    by_category[defn.category].append(defn)
                
                for category in ActionCategory:
                    actions = by_category.get(category, [])
                    if actions:
                        print(f"\n{category.value} ({len(actions)}):")
                        for defn in sorted(actions, key=lambda d: d.action_id):
                            risk_icon = _risk_icon(defn.risk_level)
                            print(f"  {risk_icon} {defn.action_id}")
                            if args.verbose:
                                print(f"      {defn.description}")
            
            # Group by risk level if requested
            elif args.by_risk:
                by_risk: dict[ActionRiskLevel, list[ActionDefinition]] = {}
                for defn in repository.all_actions:
                    if defn.risk_level not in by_risk:
                        by_risk[defn.risk_level] = []
                    by_risk[defn.risk_level].append(defn)
                
                for risk in ActionRiskLevel:
                    actions = by_risk.get(risk, [])
                    if actions:
                        print(f"\n{risk.value.upper()} ({len(actions)}):")
                        for defn in sorted(actions, key=lambda d: d.action_id):
                            print(f"  • {defn.action_id} [{defn.category.value}]")
                            if args.verbose:
                                print(f"      {defn.description}")
            
            # Flat list
            else:
                for defn in sorted(repository.all_actions, key=lambda d: d.action_id):
                    risk_icon = _risk_icon(defn.risk_level)
                    print(f"  {risk_icon} {defn.action_id} [{defn.category.value}]")
                    if args.verbose:
                        print(f"      {defn.description}")
                        print(f"      Risk: {defn.risk_level.value}")
            
            print()
            print("Risk levels: ○ minimal  ◐ low  ● moderate  ◉ high  ◈ critical")
        
        return EXIT_SUCCESS
        
    except FileNotFoundError as e:
        print(f"FILE_NOT_FOUND: {e}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR


def _risk_icon(risk: ActionRiskLevel) -> str:
    """Get icon for risk level."""
    icons = {
        ActionRiskLevel.MINIMAL: "○",
        ActionRiskLevel.LOW: "◐",
        ActionRiskLevel.MODERATE: "●",
        ActionRiskLevel.HIGH: "◉",
        ActionRiskLevel.CRITICAL: "◈",
    }
    return icons.get(risk, "?")


def cmd_generate_mocks(args: argparse.Namespace) -> int:
    """Generate mock tool implementations for testing."""
    try:
        # Load repository
        if args.repository:
            repository = ActionRepository.load(args.repository)
        else:
            repository = create_standard_repository()
        
        # Generate mock code
        lines = [
            '"""',
            'Auto-generated mock tools for APE testing.',
            f'Generated from: {"custom repository" if args.repository else "standard repository"}',
            '',
            'Usage:',
            '    from mock_tools import MOCK_TOOLS, register_all_mocks',
            '    ',
            '    # Register with orchestrator',
            '    register_all_mocks(orchestrator)',
            '    ',
            '    # Or use individual mocks',
            '    orchestrator.register_tool("read_file", MOCK_TOOLS["read_file"])',
            '"""',
            '',
            'from typing import Any',
            '',
            '',
        ]
        
        mock_functions = []
        
        for defn in sorted(repository.all_actions, key=lambda d: d.action_id):
            func_name = f"mock_{defn.action_id}"
            mock_functions.append((defn.action_id, func_name))
            
            # Build parameter list from schema
            params = []
            schema = defn.parameter_schema
            if schema and schema.get("properties"):
                required = set(schema.get("required", []))
                for param_name, param_schema in schema["properties"].items():
                    param_type = _python_type(param_schema.get("type", "any"))
                    default = param_schema.get("default")
                    if param_name in required:
                        params.append(f"{param_name}: {param_type}")
                    elif default is not None:
                        params.append(f"{param_name}: {param_type} = {repr(default)}")
                    else:
                        params.append(f"{param_name}: {param_type} = None")
            
            param_str = ", ".join(params) if params else ""
            
            # Generate function
            lines.append(f"def {func_name}({param_str}) -> Any:")
            lines.append(f'    """Mock {defn.action_id} - {defn.description}"""')
            
            # Generate appropriate mock response based on category
            if defn.category == ActionCategory.FILE_READ:
                lines.append(f'    return f"[MOCK] Contents of {{path if \'path\' in dir() else \'file\'}}"')
            elif defn.category == ActionCategory.FILE_WRITE:
                lines.append(f'    print(f"[MOCK] Would write to {{path if \'path\' in dir() else \'file\'}}")')
                lines.append('    return True')
            elif defn.category == ActionCategory.FILE_DELETE:
                lines.append(f'    print(f"[MOCK] Would delete {{path if \'path\' in dir() else \'file\'}}")')
                lines.append('    return True')
            elif defn.category == ActionCategory.NETWORK:
                lines.append(f'    return {{"mock": True, "action": "{defn.action_id}"}}')
            elif defn.category == ActionCategory.DATABASE_READ:
                lines.append('    return [{"id": 1, "mock": True}]')
            elif defn.category == ActionCategory.DATABASE_WRITE:
                lines.append('    return {"affected_rows": 1, "mock": True}')
            elif defn.category == ActionCategory.COMMUNICATION:
                lines.append(f'    print(f"[MOCK] Would send {defn.action_id}")')
                lines.append('    return {"sent": True, "mock": True}')
            elif defn.category == ActionCategory.COMPUTE:
                lines.append('    return {"result": "mock_output", "mock": True}')
            else:
                lines.append(f'    return {{"action": "{defn.action_id}", "mock": True}}')
            
            lines.append('')
            lines.append('')
        
        # Generate MOCK_TOOLS dict
        lines.append('# Dictionary of all mock tools')
        lines.append('MOCK_TOOLS = {')
        for action_id, func_name in mock_functions:
            lines.append(f'    "{action_id}": {func_name},')
        lines.append('}')
        lines.append('')
        lines.append('')
        
        # Generate helper function
        lines.append('def register_all_mocks(orchestrator) -> None:')
        lines.append('    """Register all mock tools with an APE Orchestrator."""')
        lines.append('    orchestrator.register_tools(MOCK_TOOLS)')
        lines.append('')
        
        content = '\n'.join(lines)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(content)
            print(f"✓ Generated mock tools: {args.output}")
            print(f"  {len(mock_functions)} mock functions created")
        else:
            print(content)
        
        return EXIT_SUCCESS
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR


def _python_type(json_type: str) -> str:
    """Convert JSON schema type to Python type hint."""
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }
    return type_map.get(json_type, "Any")


# =============================================================================
# Utility Commands
# =============================================================================

def cmd_version(args: argparse.Namespace) -> int:
    """Show APE version."""
    from ape import __version__
    print(f"Agent Policy Engine (APE) v{__version__}")
    return EXIT_SUCCESS


# =============================================================================
# Main Entry Point
# =============================================================================

def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ape",
        description="Agent Policy Engine - Deterministic policy enforcement for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a policy
  ape validate policies/read_only.yaml
  
  # Test a single action against policy
  ape simulate policies/read_only.yaml read_file
  
  # Test a prompt through full pipeline (v1.0.1)
  ape test-prompt policies/read_only.yaml "Read the config file"
  
  # Analyze a prompt without policy check (v1.0.1)
  ape analyze "Read config.json and delete temp files"
  
  # List available actions (v1.0.1)
  ape actions --by-category
  
  # Compare two policies
  ape diff policies/read_only.yaml policies/development.yaml
  
  # Generate mock tools for testing (v1.0.1)
  ape generate-mocks -o tests/mock_tools.py
"""
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # -------------------------------------------------------------------------
    # Policy Commands
    # -------------------------------------------------------------------------
    
    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a policy file"
    )
    validate_parser.add_argument("policy", help="Path to policy YAML file")
    
    # simulate command
    simulate_parser = subparsers.add_parser(
        "simulate",
        help="Simulate policy evaluation for an action"
    )
    simulate_parser.add_argument("policy", help="Path to policy YAML file")
    simulate_parser.add_argument("action", help="Action ID to evaluate")
    simulate_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    simulate_parser.add_argument("--verbose", "-V", action="store_true", help="Show detailed output")
    
    # simulate-batch command
    batch_parser = subparsers.add_parser(
        "simulate-batch",
        help="Simulate policy evaluation for multiple actions"
    )
    batch_parser.add_argument("policy", help="Path to policy YAML file")
    batch_parser.add_argument("actions", nargs="*", help="Action IDs to evaluate")
    batch_parser.add_argument("--file", "-f", dest="actions_file", help="File containing action IDs (one per line)")
    batch_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    # info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show information about a policy"
    )
    info_parser.add_argument("policy", help="Path to policy YAML file")
    info_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    # diff command
    diff_parser = subparsers.add_parser(
        "diff",
        help="Compare two policy files"
    )
    diff_parser.add_argument("policy1", help="First policy file")
    diff_parser.add_argument("policy2", help="Second policy file")
    diff_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    # -------------------------------------------------------------------------
    # MCP Commands
    # -------------------------------------------------------------------------
    
    # mcp-scan command
    mcp_scan_parser = subparsers.add_parser(
        "mcp-scan",
        help="Scan MCP configuration and generate a policy"
    )
    mcp_scan_parser.add_argument("mcp_config", help="Path to MCP configuration JSON file")
    mcp_scan_parser.add_argument("--output", "-o", help="Output policy file path")
    mcp_scan_parser.add_argument("--name", "-n", default="mcp_generated", help="Policy name")
    mcp_scan_parser.add_argument("--allow-unlisted", action="store_true", help="Allow actions not in MCP config")
    
    # mcp-info command
    mcp_info_parser = subparsers.add_parser(
        "mcp-info",
        help="Show information about an MCP configuration"
    )
    mcp_info_parser.add_argument("mcp_config", help="Path to MCP configuration JSON file")
    mcp_info_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    # -------------------------------------------------------------------------
    # v1.0.1 Commands - Intent & Prompt Testing
    # -------------------------------------------------------------------------
    
    # test-prompt command
    test_prompt_parser = subparsers.add_parser(
        "test-prompt",
        help="Test a prompt through the full intent compilation pipeline (v1.0.1)"
    )
    test_prompt_parser.add_argument("policy", help="Path to policy YAML file")
    test_prompt_parser.add_argument("prompt", help="Natural language prompt to test")
    test_prompt_parser.add_argument("--repository", "-r", help="Path to custom action repository YAML")
    test_prompt_parser.add_argument("--max-risk", "-m", help="Maximum risk level (minimal/low/moderate/high/critical)")
    test_prompt_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a prompt to see extracted signals and actions (v1.0.1)"
    )
    analyze_parser.add_argument("prompt", help="Natural language prompt to analyze")
    analyze_parser.add_argument("--repository", "-r", help="Path to custom action repository YAML")
    analyze_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    # actions command
    actions_parser = subparsers.add_parser(
        "actions",
        help="List actions in the Action Repository (v1.0.1)"
    )
    actions_parser.add_argument("--repository", "-r", help="Path to custom action repository YAML")
    actions_parser.add_argument("--by-category", "-c", action="store_true", help="Group by category")
    actions_parser.add_argument("--by-risk", "-R", action="store_true", help="Group by risk level")
    actions_parser.add_argument("--verbose", "-V", action="store_true", help="Show descriptions")
    actions_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    # generate-mocks command
    generate_mocks_parser = subparsers.add_parser(
        "generate-mocks",
        help="Generate mock tool implementations for testing (v1.0.1)"
    )
    generate_mocks_parser.add_argument("--repository", "-r", help="Path to custom action repository YAML")
    generate_mocks_parser.add_argument("--output", "-o", help="Output file path (prints to stdout if not specified)")
    
    # -------------------------------------------------------------------------
    # Parse and dispatch
    # -------------------------------------------------------------------------
    
    args = parser.parse_args(argv)
    
    if args.version:
        return cmd_version(args)
    
    if not args.command:
        parser.print_help()
        return EXIT_SUCCESS
    
    # Dispatch to command handler
    handlers = {
        "validate": cmd_validate,
        "simulate": cmd_simulate,
        "simulate-batch": cmd_simulate_batch,
        "info": cmd_info,
        "diff": cmd_diff,
        "mcp-scan": cmd_mcp_scan,
        "mcp-info": cmd_mcp_info,
        "test-prompt": cmd_test_prompt,
        "analyze": cmd_analyze,
        "actions": cmd_actions,
        "generate-mocks": cmd_generate_mocks,
    }
    
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    
    parser.print_help()
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
