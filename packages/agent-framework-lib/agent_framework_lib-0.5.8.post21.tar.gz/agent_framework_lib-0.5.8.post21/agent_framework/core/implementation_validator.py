"""
Implementation Validator for Agent Framework

This module provides validation utilities to verify that a new agent implementation
correctly follows the framework's requirements and best practices.

Usage:
    from agent_framework.core.implementation_validator import validate_agent_implementation
    
    # Validate your agent class
    report = await validate_agent_implementation(MyNewAgent)
    print(report)
    
    # Or validate an instance
    agent = MyNewAgent(agent_id="test", name="Test", description="Test agent")
    report = await validate_agent_implementation(agent)
    print(report)
"""

import asyncio
import inspect
import logging
from abc import ABC
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, get_type_hints

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Must fix - will cause runtime failures
    WARNING = "warning"  # Should fix - may cause issues
    INFO = "info"        # Suggestion - best practice


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    category: str
    message: str
    severity: ValidationSeverity
    suggestion: str | None = None
    
    def __str__(self) -> str:
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[self.severity.value]
        result = f"{icon} [{self.category}] {self.message}"
        if self.suggestion:
            result += f"\n   💡 {self.suggestion}"
        return result


@dataclass
class ValidationReport:
    """Complete validation report for an agent implementation."""
    agent_class_name: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    issues: list[ValidationIssue] = field(default_factory=list)
    checks_passed: int = 0
    checks_failed: int = 0
    checks_warned: int = 0
    
    @property
    def is_valid(self) -> bool:
        """Returns True if no errors were found."""
        return self.checks_failed == 0
    
    @property
    def score(self) -> str:
        """Returns a score based on issues found."""
        total = self.checks_passed + self.checks_failed + self.checks_warned
        if total == 0:
            return "N/A"
        pct = (self.checks_passed / total) * 100
        if pct >= 90:
            return f"✅ Excellent ({pct:.0f}%)"
        elif pct >= 70:
            return f"🟡 Good ({pct:.0f}%)"
        elif pct >= 50:
            return f"🟠 Needs Work ({pct:.0f}%)"
        else:
            return f"🔴 Critical ({pct:.0f}%)"
    
    def add_pass(self, category: str, message: str) -> None:
        """Record a passed check."""
        self.checks_passed += 1
        self.issues.append(ValidationIssue(
            category=category,
            message=message,
            severity=ValidationSeverity.INFO,
        ))
    
    def add_error(self, category: str, message: str, suggestion: str | None = None) -> None:
        """Record a failed check (error)."""
        self.checks_failed += 1
        self.issues.append(ValidationIssue(
            category=category,
            message=message,
            severity=ValidationSeverity.ERROR,
            suggestion=suggestion,
        ))
    
    def add_warning(self, category: str, message: str, suggestion: str | None = None) -> None:
        """Record a warning."""
        self.checks_warned += 1
        self.issues.append(ValidationIssue(
            category=category,
            message=message,
            severity=ValidationSeverity.WARNING,
            suggestion=suggestion,
        ))
    
    def __str__(self) -> str:
        lines = [
            "=" * 70,
            f"🔍 VALIDATION REPORT: {self.agent_class_name}",
            f"   Generated: {self.timestamp}",
            "=" * 70,
            "",
            f"📊 Score: {self.score}",
            f"   ✅ Passed: {self.checks_passed}",
            f"   ❌ Errors: {self.checks_failed}",
            f"   ⚠️ Warnings: {self.checks_warned}",
            "",
        ]
        
        # Group issues by severity
        errors = [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
        
        if errors:
            lines.append("❌ ERRORS (must fix):")
            lines.append("-" * 40)
            for issue in errors:
                lines.append(str(issue))
            lines.append("")
        
        if warnings:
            lines.append("⚠️ WARNINGS (should fix):")
            lines.append("-" * 40)
            for issue in warnings:
                lines.append(str(issue))
            lines.append("")
        
        if self.is_valid:
            lines.append("✅ Implementation is VALID")
        else:
            lines.append("❌ Implementation has ERRORS - please fix before use")
        
        lines.append("=" * 70)
        return "\n".join(lines)


class AgentImplementationValidator:
    """Validates agent implementations against framework requirements."""
    
    # Required abstract methods from BaseAgent
    REQUIRED_METHODS = [
        "get_agent_prompt",
        "get_agent_tools", 
        "initialize_agent",
        "create_fresh_context",
        "serialize_context",
        "deserialize_context",
        "run_agent",
    ]
    
    # Methods that should NOT be overridden
    FINAL_METHODS = [
        "handle_message_stream",  # Orchestration in BaseAgent
    ]
    
    # Required attributes
    REQUIRED_ATTRIBUTES = [
        "_agent_instance",
    ]
    
    # Recommended attributes for full functionality
    RECOMMENDED_ATTRIBUTES = [
        "_session_storage",
        "_memory_adapter", 
        "_current_memory",
        "_current_session_id",
        "_current_user_id",
        "_current_model",
        "_metrics_enabled",
        "_metrics_collector",
        "_display_config_manager",
    ]
    
    def __init__(self, agent_class_or_instance: Any):
        """Initialize validator with agent class or instance."""
        if isinstance(agent_class_or_instance, type):
            self.agent_class = agent_class_or_instance
            self.agent_instance = None
        else:
            self.agent_class = type(agent_class_or_instance)
            self.agent_instance = agent_class_or_instance
        
        self.report = ValidationReport(agent_class_name=self.agent_class.__name__)
    
    async def validate(self) -> ValidationReport:
        """Run all validation checks and return report."""
        # 1. Check inheritance
        self._check_inheritance()
        
        # 2. Check required methods
        self._check_required_methods()
        
        # 3. Check method signatures
        self._check_method_signatures()
        
        # 4. Check final methods not overridden
        self._check_final_methods()
        
        # 5. Check attributes
        self._check_attributes()
        
        # 6. Check async methods
        self._check_async_methods()
        
        # 7. If we have an instance, run runtime checks
        if self.agent_instance:
            await self._check_runtime_behavior()
        
        # 8. Check process_streaming_event implementation
        self._check_streaming_event_handler()
        
        # 9. Check memory adapter pattern
        self._check_memory_adapter()
        
        return self.report
    
    def _check_inheritance(self) -> None:
        """Check that agent inherits from BaseAgent."""
        from agent_framework.core.base_agent import BaseAgent
        from agent_framework.core.agent_interface import AgentInterface
        
        if issubclass(self.agent_class, BaseAgent):
            self.report.add_pass("inheritance", f"{self.agent_class.__name__} inherits from BaseAgent")
        elif issubclass(self.agent_class, AgentInterface):
            self.report.add_warning(
                "inheritance",
                f"{self.agent_class.__name__} inherits from AgentInterface but not BaseAgent",
                "Consider inheriting from BaseAgent to get streaming orchestration for free"
            )
        else:
            self.report.add_error(
                "inheritance",
                f"{self.agent_class.__name__} does not inherit from AgentInterface",
                "Your agent must inherit from BaseAgent or at minimum AgentInterface"
            )
    
    def _check_required_methods(self) -> None:
        """Check that all required methods are implemented."""
        for method_name in self.REQUIRED_METHODS:
            method = getattr(self.agent_class, method_name, None)
            
            if method is None:
                self.report.add_error(
                    "required_method",
                    f"Missing required method: {method_name}()",
                    f"Implement {method_name}() in your agent class"
                )
            elif self._is_abstract_method(method):
                self.report.add_error(
                    "required_method",
                    f"Method {method_name}() is still abstract (not implemented)",
                    f"Provide a concrete implementation of {method_name}()"
                )
            else:
                self.report.add_pass("required_method", f"Method {method_name}() is implemented")
    
    def _is_abstract_method(self, method: Any) -> bool:
        """Check if a method is abstract."""
        return getattr(method, "__isabstractmethod__", False)
    
    def _check_method_signatures(self) -> None:
        """Check that method signatures match expected patterns."""
        # Check run_agent signature
        run_agent = getattr(self.agent_class, "run_agent", None)
        if run_agent:
            sig = inspect.signature(run_agent)
            params = list(sig.parameters.keys())
            
            expected = ["self", "query", "ctx", "stream"]
            if params[:4] != expected:
                self.report.add_warning(
                    "signature",
                    f"run_agent() signature doesn't match expected: {expected}",
                    "Ensure run_agent(self, query: str, ctx: Any, stream: bool = False)"
                )
            else:
                self.report.add_pass("signature", "run_agent() has correct signature")
            
            # Check return type annotation
            hints = get_type_hints(run_agent) if hasattr(run_agent, "__annotations__") else {}
            return_hint = hints.get("return", None)
            if return_hint is None:
                self.report.add_warning(
                    "signature",
                    "run_agent() missing return type annotation",
                    "Add -> str | AsyncGenerator return type hint"
                )
        
        # Check process_streaming_event signature
        process_event = getattr(self.agent_class, "process_streaming_event", None)
        if process_event:
            sig = inspect.signature(process_event)
            params = list(sig.parameters.keys())
            
            if "event" not in params:
                self.report.add_warning(
                    "signature",
                    "process_streaming_event() should have 'event' parameter",
                    "Signature should be: process_streaming_event(self, event: Any)"
                )
    
    def _check_final_methods(self) -> None:
        """Check that final methods are not overridden."""
        from agent_framework.core.base_agent import BaseAgent
        
        for method_name in self.FINAL_METHODS:
            agent_method = getattr(self.agent_class, method_name, None)
            base_method = getattr(BaseAgent, method_name, None)
            
            if agent_method is None:
                continue
            
            # Check if method is defined in the agent class itself (not inherited)
            if method_name in self.agent_class.__dict__:
                self.report.add_error(
                    "final_method",
                    f"Method {method_name}() should NOT be overridden",
                    f"Remove {method_name}() override. Use run_agent() and process_streaming_event() instead."
                )
            else:
                self.report.add_pass("final_method", f"Method {method_name}() correctly inherited")
    
    def _check_attributes(self) -> None:
        """Check for required and recommended attributes."""
        # Check __init__ for attribute initialization
        init_source = inspect.getsource(self.agent_class.__init__) if hasattr(self.agent_class, "__init__") else ""
        
        for attr in self.REQUIRED_ATTRIBUTES:
            if attr in init_source or (self.agent_instance and hasattr(self.agent_instance, attr)):
                self.report.add_pass("attribute", f"Required attribute {attr} is initialized")
            else:
                self.report.add_error(
                    "attribute",
                    f"Missing required attribute: {attr}",
                    f"Initialize {attr} in __init__()"
                )
        
        for attr in self.RECOMMENDED_ATTRIBUTES:
            if attr in init_source or (self.agent_instance and hasattr(self.agent_instance, attr)):
                self.report.add_pass("attribute", f"Recommended attribute {attr} is present")
            else:
                self.report.add_warning(
                    "attribute",
                    f"Missing recommended attribute: {attr}",
                    f"Consider adding {attr} for full functionality"
                )
    
    def _check_async_methods(self) -> None:
        """Check that I/O methods are async."""
        async_required = [
            "initialize_agent",
            "run_agent",
            "configure_session",
            "handle_message",
            "handle_message_stream",
            "get_state",
            "load_state",
        ]
        
        for method_name in async_required:
            method = getattr(self.agent_class, method_name, None)
            if method is None:
                continue
            
            if asyncio.iscoroutinefunction(method):
                self.report.add_pass("async", f"Method {method_name}() is async")
            else:
                # Check if it's inherited and async in parent
                from agent_framework.core.base_agent import BaseAgent
                parent_method = getattr(BaseAgent, method_name, None)
                if parent_method and asyncio.iscoroutinefunction(parent_method):
                    if method_name not in self.agent_class.__dict__:
                        self.report.add_pass("async", f"Method {method_name}() inherited as async")
                    else:
                        self.report.add_error(
                            "async",
                            f"Method {method_name}() must be async",
                            f"Change to: async def {method_name}(...)"
                        )
    
    async def _check_runtime_behavior(self) -> None:
        """Run runtime checks on an agent instance."""
        if not self.agent_instance:
            return
        
        # Check get_agent_prompt returns non-empty string
        try:
            prompt = self.agent_instance.get_agent_prompt()
            if prompt and isinstance(prompt, str) and len(prompt) > 10:
                self.report.add_pass("runtime", "get_agent_prompt() returns valid prompt")
            else:
                self.report.add_warning(
                    "runtime",
                    "get_agent_prompt() returns empty or very short prompt",
                    "Provide a meaningful system prompt"
                )
        except Exception as e:
            self.report.add_error("runtime", f"get_agent_prompt() raised exception: {e}")
        
        # Check get_agent_tools returns list
        try:
            tools = self.agent_instance.get_agent_tools()
            if isinstance(tools, list):
                self.report.add_pass("runtime", f"get_agent_tools() returns list with {len(tools)} tools")
            else:
                self.report.add_error(
                    "runtime",
                    f"get_agent_tools() should return list, got {type(tools).__name__}",
                    "Return a list of callable tools"
                )
        except Exception as e:
            self.report.add_error("runtime", f"get_agent_tools() raised exception: {e}")
        
        # Check create_fresh_context
        try:
            ctx = self.agent_instance.create_fresh_context()
            if ctx is not None:
                self.report.add_pass("runtime", "create_fresh_context() returns context object")
            else:
                self.report.add_warning(
                    "runtime",
                    "create_fresh_context() returns None",
                    "Consider returning an empty dict {} if no context needed"
                )
        except Exception as e:
            self.report.add_error("runtime", f"create_fresh_context() raised exception: {e}")
        
        # Check serialize/deserialize roundtrip
        try:
            ctx = self.agent_instance.create_fresh_context()
            if ctx is not None:
                serialized = self.agent_instance.serialize_context(ctx)
                if isinstance(serialized, dict):
                    deserialized = self.agent_instance.deserialize_context(serialized)
                    self.report.add_pass("runtime", "Context serialize/deserialize roundtrip works")
                else:
                    self.report.add_error(
                        "runtime",
                        f"serialize_context() should return dict, got {type(serialized).__name__}",
                        "Return a JSON-serializable dictionary"
                    )
        except Exception as e:
            self.report.add_error("runtime", f"Context roundtrip failed: {e}")
    
    def _check_streaming_event_handler(self) -> None:
        """Check process_streaming_event implementation."""
        method = getattr(self.agent_class, "process_streaming_event", None)
        
        if method is None:
            self.report.add_warning(
                "streaming",
                "process_streaming_event() not implemented",
                "Implement to convert framework events to unified format"
            )
            return
        
        # Check if it's overridden (not just inherited)
        from agent_framework.core.base_agent import BaseAgent
        if method is getattr(BaseAgent, "process_streaming_event", None):
            self.report.add_warning(
                "streaming",
                "process_streaming_event() not overridden (using base implementation)",
                "Override to handle your framework's specific event types"
            )
        else:
            self.report.add_pass("streaming", "process_streaming_event() is implemented")
            
            # Check source code for required event types
            try:
                source = inspect.getsource(method)
                
                event_types = ["chunk", "tool_call", "tool_result"]
                for event_type in event_types:
                    if f'"{event_type}"' in source or f"'{event_type}'" in source:
                        self.report.add_pass("streaming", f"Handles '{event_type}' event type")
                    else:
                        self.report.add_warning(
                            "streaming",
                            f"May not handle '{event_type}' event type",
                            f"Ensure process_streaming_event returns {{'type': '{event_type}', ...}}"
                        )
            except (OSError, TypeError):
                pass  # Can't get source, skip this check
    
    def _check_memory_adapter(self) -> None:
        """Check memory adapter implementation."""
        # Check if set_session_storage is implemented
        method = getattr(self.agent_class, "set_session_storage", None)
        
        if method is None:
            self.report.add_warning(
                "memory",
                "set_session_storage() not implemented",
                "Implement to enable conversation history loading"
            )
        else:
            self.report.add_pass("memory", "set_session_storage() is implemented")
        
        # Check for memory adapter initialization
        init_source = ""
        try:
            init_source = inspect.getsource(self.agent_class.__init__)
        except (OSError, TypeError):
            pass
        
        if "_memory_adapter" in init_source:
            self.report.add_pass("memory", "Memory adapter attribute initialized")
        else:
            self.report.add_warning(
                "memory",
                "No memory adapter initialization found",
                "Initialize _memory_adapter in __init__ or set_session_storage()"
            )


async def validate_agent_implementation(
    agent_class_or_instance: Any,
    verbose: bool = True
) -> ValidationReport:
    """
    Validate an agent implementation against framework requirements.
    
    Args:
        agent_class_or_instance: Agent class or instance to validate
        verbose: If True, print the report to stdout
        
    Returns:
        ValidationReport with all findings
        
    Example:
        >>> from my_agent import MyNewAgent
        >>> report = await validate_agent_implementation(MyNewAgent)
        >>> if not report.is_valid:
        ...     print("Fix errors before deploying!")
    """
    validator = AgentImplementationValidator(agent_class_or_instance)
    report = await validator.validate()
    
    if verbose:
        print(report)
    
    return report


def validate_agent_implementation_sync(
    agent_class_or_instance: Any,
    verbose: bool = True
) -> ValidationReport:
    """
    Synchronous wrapper for validate_agent_implementation.
    
    Useful for quick validation in scripts or notebooks.
    """
    return asyncio.run(validate_agent_implementation(agent_class_or_instance, verbose))
