"""
Automation - Robust multi-step automation runner with retry logic.

Provides a maintainable, error-resistant way to execute UI automation workflows.
Supports retries, waits, conditional steps, and detailed logging.

Usage:
    from core.automation import Automation, Step

    auto = Automation()
    auto.run([
        Step("open", app="clock"),
        Step("tap", text="Alarm"),
        Step("tap", desc="Add alarm"),
        Step("tap", text="11"),
        Step("tap", text="10"),
        Step("tap", text="OK"),
    ])
"""

import json
import re
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union

from core.android import Android

if TYPE_CHECKING:
    from core.variables import VariableContext
from core.exceptions import (
    AssertionFailedError,
    BreakException,
    ContinueException,
    DittoMationError,
    ElementNotFoundError,
    InvalidControlFlowError,
    LoopLimitError,
)
from core.logging_config import get_logger

logger = get_logger("automation")


class StepType(Enum):
    """Supported step types."""

    # Basic actions
    TAP = "tap"
    LONG_PRESS = "long_press"
    SWIPE = "swipe"
    SCROLL = "scroll"
    TYPE = "type"
    PRESS = "press"
    OPEN = "open"
    WAIT = "wait"
    WAIT_FOR = "wait_for"
    ASSERT_EXISTS = "assert_exists"
    ASSERT_NOT_EXISTS = "assert_not_exists"
    SCREENSHOT = "screenshot"
    CONDITIONAL = "conditional"

    # Variable operations
    SET_VARIABLE = "set_variable"
    EXTRACT = "extract"

    # Control flow
    IF = "if"
    FOR = "for"
    WHILE = "while"
    UNTIL = "until"
    BREAK = "break"
    CONTINUE = "continue"

    # Utility
    LOG = "log"
    ASSERT = "assert"


class StepStatus(Enum):
    """Step execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class StepResult:
    """Result of a step execution."""

    step_index: int
    step_type: str
    status: StepStatus
    message: str = ""
    attempts: int = 1
    duration_ms: float = 0
    confidence: Optional[float] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_index": self.step_index,
            "step_type": self.step_type,
            "status": self.status.value,
            "message": self.message,
            "attempts": self.attempts,
            "duration_ms": round(self.duration_ms, 2),
            "confidence": self.confidence,
            "error": self.error,
        }


@dataclass
class Step:
    """
    A single automation step.

    Attributes:
        action: Step type (tap, swipe, type, open, wait, if, for, while, etc.)
        text: Element text to find
        id: Element resource-id to find
        desc: Element content-description to find
        x: X coordinate (for coordinate-based actions)
        y: Y coordinate (for coordinate-based actions)
        app: App name (for open action)
        value: Value for type action or key for press action
        direction: Direction for swipe/scroll (up, down, left, right)
        timeout: Timeout in seconds for element search
        min_confidence: Minimum confidence for element matching (0.0-1.0)
        retries: Number of retry attempts on failure
        retry_delay: Delay between retries in seconds
        wait_before: Wait time before executing step (seconds)
        wait_after: Wait time after executing step (seconds)
        optional: If True, failure doesn't stop execution
        condition: Callable that returns True if step should execute
        on_failure: Action on failure ("stop", "continue", "retry")
        description: Human-readable description for logging

        # Variable operations
        variable: Variable name for set_variable/extract actions
        expr: Expression for set_variable (evaluated) or condition expression
        extract_source: Source for extract action (text, attribute, bounds)
        extract_attr: Attribute name for extract (when extract_source='attribute')
        regex: Regex pattern for extract action

        # Control flow
        then_steps: Steps to execute if condition is true (for if action)
        else_steps: Steps to execute if condition is false (for if action)
        elif_blocks: List of {condition, steps} for elif clauses
        loop_steps: Steps to execute in loop (for, while, until)
        items: Items expression for for-loop
        item_var: Variable name for current item in for-loop
        index_var: Variable name for current index in for-loop
        counter_var: Variable name for iteration counter
        max_iterations: Maximum iterations for loops

        # Utility
        message: Message for log/assert actions
        level: Log level (debug, info, warning, error)
    """

    action: str
    text: Optional[str] = None
    id: Optional[str] = None
    desc: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    app: Optional[str] = None
    value: Optional[str] = None
    direction: Optional[str] = None
    timeout: float = 5.0
    min_confidence: float = 0.3
    retries: int = 2
    retry_delay: float = 1.0
    wait_before: float = 0.0
    wait_after: float = 0.3
    optional: bool = False
    condition: Optional[Callable[["Android"], bool]] = None
    on_failure: str = "stop"
    description: Optional[str] = None

    # Variable operations
    variable: Optional[str] = None
    expr: Optional[str] = None
    extract_source: Optional[str] = None
    extract_attr: Optional[str] = None
    regex: Optional[str] = None

    # Control flow
    then_steps: Optional[List[Dict[str, Any]]] = None
    else_steps: Optional[List[Dict[str, Any]]] = None
    elif_blocks: Optional[List[Dict[str, Any]]] = None
    loop_steps: Optional[List[Dict[str, Any]]] = None
    items: Optional[str] = None
    item_var: Optional[str] = None
    index_var: Optional[str] = None
    counter_var: Optional[str] = None
    max_iterations: int = 100

    # Utility
    message: Optional[str] = None
    level: str = "info"

    def __post_init__(self):
        """Validate step configuration."""
        valid_actions = {t.value for t in StepType}
        if self.action not in valid_actions:
            raise ValueError(f"Invalid action '{self.action}'. Valid: {valid_actions}")

        if self.on_failure not in ("stop", "continue", "retry"):
            raise ValueError(f"Invalid on_failure '{self.on_failure}'")

        # Validate control flow specific requirements
        if self.action == "if" and not self.expr and not hasattr(self, "_condition_str"):
            # Condition can be passed via 'condition' key in JSON, stored in expr
            pass  # Will be validated during execution

        if self.action == "for" and not self.items:
            pass  # Will be validated during execution

        if self.action in ("while", "until") and not self.expr:
            pass  # Will be validated during execution

    def get_target_description(self) -> str:
        """Get human-readable description of target."""
        if self.description:
            return self.description

        parts = [self.action.upper()]

        if self.text:
            parts.append(f'text="{self.text}"')
        if self.id:
            parts.append(f'id="{self.id}"')
        if self.desc:
            parts.append(f'desc="{self.desc}"')
        if self.x is not None and self.y is not None:
            parts.append(f"@({self.x}, {self.y})")
        if self.app:
            parts.append(f'app="{self.app}"')
        if self.value:
            parts.append(
                f'value="{self.value[:20]}..."'
                if len(self.value or "") > 20
                else f'value="{self.value}"'
            )
        if self.direction:
            parts.append(f"direction={self.direction}")

        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excludes callable and None values)."""
        result = {}
        # Fields to always exclude
        exclude_fields = {"condition"}
        # Fields with default values that shouldn't be included if at default
        default_fields = {
            "timeout": 5.0,
            "min_confidence": 0.3,
            "retries": 2,
            "retry_delay": 1.0,
            "wait_before": 0.0,
            "wait_after": 0.3,
            "optional": False,
            "on_failure": "stop",
            "max_iterations": 100,
            "level": "info",
        }

        for key, val in asdict(self).items():
            if key in exclude_fields:
                continue
            if val is None:
                continue
            # Skip default values for cleaner output
            if key in default_fields and val == default_fields[key]:
                continue
            result[key] = val
        return result


@dataclass
class AutomationResult:
    """Result of full automation run."""

    success: bool
    total_steps: int
    executed_steps: int
    failed_steps: int
    skipped_steps: int
    duration_ms: float
    step_results: List[StepResult] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "total_steps": self.total_steps,
            "executed_steps": self.executed_steps,
            "failed_steps": self.failed_steps,
            "skipped_steps": self.skipped_steps,
            "duration_ms": round(self.duration_ms, 2),
            "step_results": [r.to_dict() for r in self.step_results],
            "error": self.error,
        }

    def summary(self) -> str:
        """Get human-readable summary."""
        status = "SUCCESS" if self.success else "FAILED"
        lines = [
            f"Automation {status}",
            f"  Steps: {self.executed_steps}/{self.total_steps} executed",
            f"  Failed: {self.failed_steps}, Skipped: {self.skipped_steps}",
            f"  Duration: {self.duration_ms:.0f}ms",
        ]
        if self.error:
            lines.append(f"  Error: {self.error}")
        return "\n".join(lines)


class Automation:
    """
    Robust automation runner with retry logic and error handling.

    Features:
    - Automatic retries with configurable delay
    - Wait for elements with timeout
    - Conditional step execution
    - Detailed execution logging
    - Step-by-step result tracking

    Example:
        auto = Automation()
        result = auto.run([
            Step("open", app="clock"),
            Step("wait", timeout=2.0),
            Step("tap", text="Alarm", retries=3),
            Step("tap", desc="Add alarm"),
        ])

        if result.success:
            print("Automation completed!")
        else:
            print(f"Failed: {result.error}")
    """

    def __init__(
        self,
        device: Optional[str] = None,
        min_confidence: float = 0.3,
        default_timeout: float = 5.0,
        default_retries: int = 2,
        step_delay: float = 0.3,
        stop_on_failure: bool = True,
        screenshot_on_failure: bool = False,
        initial_vars: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize automation runner.

        Args:
            device: Device serial (auto-detect if None)
            min_confidence: Default minimum confidence for element matching
            default_timeout: Default timeout for element search
            default_retries: Default retry count per step
            step_delay: Default delay between steps (seconds)
            stop_on_failure: Stop execution on first failure
            screenshot_on_failure: Take screenshot when step fails
            initial_vars: Initial variables to set in context
        """
        self.android = Android(device=device, min_confidence=min_confidence)
        self.min_confidence = min_confidence
        self.default_timeout = default_timeout
        self.default_retries = default_retries
        self.step_delay = step_delay
        self.stop_on_failure = stop_on_failure
        self.screenshot_on_failure = screenshot_on_failure

        self._step_results: List[StepResult] = []
        self._current_step: int = 0

        # Variable and expression support
        from core.control_flow import ControlFlowExecutor
        from core.expressions import SafeExpressionEngine
        from core.variables import VariableContext, VariableResolver

        self._context = VariableContext(initial_vars)
        self._resolver = VariableResolver(self._context)
        self._expr_engine = SafeExpressionEngine(self._context, self.android)
        self._control_flow: Optional[ControlFlowExecutor] = None
        self._in_loop = False
        self._loop_depth = 0

        logger.info(f"Automation initialized for device: {self.android.device}")

    def run(
        self, steps: List[Step], initial_vars: Optional[Dict[str, Any]] = None
    ) -> AutomationResult:
        """
        Execute a list of automation steps.

        Args:
            steps: List of Step objects to execute
            initial_vars: Optional additional variables to set before running

        Returns:
            AutomationResult with execution details
        """
        start_time = time.time()
        self._step_results = []
        self._current_step = 0

        # Update context with any additional initial vars
        if initial_vars:
            self._context.update(initial_vars)

        # Initialize control flow executor
        from core.control_flow import ControlFlowExecutor

        self._control_flow = ControlFlowExecutor(
            self._expr_engine, self._context, self._execute_steps_internal
        )

        executed = 0
        failed = 0
        skipped = 0
        error_msg = None

        logger.info(f"Starting automation with {len(steps)} steps")

        try:
            results = self._execute_steps_internal(steps)
            for result in results:
                if result.status == StepStatus.SUCCESS:
                    executed += 1
                elif result.status == StepStatus.SKIPPED:
                    skipped += 1
                else:
                    failed += 1

        except BreakException:
            if not self._in_loop:
                error_msg = "Break statement outside of loop"
                logger.error(error_msg)
        except ContinueException:
            if not self._in_loop:
                error_msg = "Continue statement outside of loop"
                logger.error(error_msg)
        except Exception as e:
            error_msg = f"Automation error: {str(e)}"
            logger.exception(error_msg)

        duration = (time.time() - start_time) * 1000
        success = failed == 0 and error_msg is None

        result = AutomationResult(
            success=success,
            total_steps=len(steps),
            executed_steps=executed,
            failed_steps=failed,
            skipped_steps=skipped,
            duration_ms=duration,
            step_results=self._step_results,
            error=error_msg,
        )

        logger.info(result.summary())
        return result

    def _execute_steps_internal(self, steps: List[Step]) -> List[StepResult]:
        """
        Internal method to execute steps, used by control flow.

        Args:
            steps: Steps to execute

        Returns:
            List of step results
        """
        results = []

        for i, step in enumerate(steps):
            self._current_step = i

            # Resolve variables in step
            resolved_step = self._resolve_step_variables(step)

            # Check condition (callable)
            if resolved_step.condition is not None:
                try:
                    should_run = resolved_step.condition(self.android)
                    if not should_run:
                        result = StepResult(
                            step_index=i,
                            step_type=resolved_step.action,
                            status=StepStatus.SKIPPED,
                            message="Condition not met",
                        )
                        self._step_results.append(result)
                        results.append(result)
                        logger.debug(f"Step {i+1} skipped: condition not met")
                        continue
                except Exception as e:
                    logger.warning(f"Step {i+1} condition check failed: {e}")

            # Execute step with retries
            result = self._execute_step(i, resolved_step)
            self._step_results.append(result)
            results.append(result)

            if result.status == StepStatus.FAILED:
                if self.screenshot_on_failure:
                    try:
                        self.android.screenshot(f"failure_step_{i+1}.png")
                    except Exception:
                        pass

                if resolved_step.on_failure == "stop" or (
                    self.stop_on_failure and not resolved_step.optional
                ):
                    error_msg = f"Step {i+1} failed: {result.error}"
                    logger.error(error_msg)
                    break

        return results

    def _resolve_step_variables(self, step: Step) -> Step:
        """
        Resolve {{variable}} placeholders in a step.

        Args:
            step: Step with potential variable placeholders

        Returns:
            New Step with resolved values
        """
        if not self._resolver:
            return step

        # Create a dict of the step
        step_dict = step.to_dict()

        # Fields that should have variables resolved
        resolvable_fields = {
            "text",
            "id",
            "desc",
            "value",
            "app",
            "direction",
            "description",
            "message",
            "variable",
            "expr",
            "items",
            "item_var",
            "index_var",
            "counter_var",
            "extract_attr",
            "regex",
        }

        # Don't pre-resolve expr/items for control flow actions - they need
        # dynamic evaluation (while/until conditions must be re-evaluated each iteration,
        # if/for expressions need the expression engine to handle variable resolution)
        control_flow_actions = {"if", "while", "until", "for"}
        if step.action in control_flow_actions:
            resolvable_fields = resolvable_fields - {"expr", "items"}

        for field_name in resolvable_fields:
            if field_name in step_dict and step_dict[field_name] is not None:
                original = str(step_dict[field_name])
                if self._resolver.has_variables(original):
                    step_dict[field_name] = self._resolver.resolve_string(original)

        # Preserve the original condition callable
        step_dict["condition"] = step.condition

        return Step(**step_dict)

    def _execute_step(self, index: int, step: Step) -> StepResult:
        """Execute a single step with retry logic."""
        start_time = time.time()
        attempts = 0
        max_attempts = step.retries + 1
        last_error = None
        confidence = None

        # Wait before step
        if step.wait_before > 0:
            time.sleep(step.wait_before)

        while attempts < max_attempts:
            attempts += 1

            try:
                logger.debug(
                    f"Step {index+1}/{self._current_step+1}: {step.get_target_description()} (attempt {attempts})"
                )

                success, confidence = self._do_step(step)

                if success:
                    # Wait after step
                    if step.wait_after > 0:
                        time.sleep(step.wait_after)

                    duration = (time.time() - start_time) * 1000
                    return StepResult(
                        step_index=index,
                        step_type=step.action,
                        status=StepStatus.SUCCESS,
                        message=step.get_target_description(),
                        attempts=attempts,
                        duration_ms=duration,
                        confidence=confidence,
                    )
                else:
                    last_error = "Action returned False"

            except ElementNotFoundError as e:
                last_error = f"Element not found: {e.message}"
            except (BreakException, ContinueException):
                # Control flow exceptions must propagate to enclosing loop
                raise
            except DittoMationError as e:
                last_error = e.message
            except Exception as e:
                last_error = str(e)

            # Retry logic
            if attempts < max_attempts:
                logger.warning(
                    f"Step {index+1} attempt {attempts} failed: {last_error}. Retrying..."
                )
                time.sleep(step.retry_delay)

        # All attempts failed
        duration = (time.time() - start_time) * 1000
        return StepResult(
            step_index=index,
            step_type=step.action,
            status=StepStatus.FAILED,
            message=step.get_target_description(),
            attempts=attempts,
            duration_ms=duration,
            confidence=confidence,
            error=last_error,
        )

    def _do_step(self, step: Step) -> Tuple[bool, Optional[float]]:
        """
        Execute the actual step action.

        Returns:
            Tuple of (success, confidence_score)
        """
        action = step.action

        if action == "tap":
            if step.x is not None and step.y is not None:
                return self.android.tap(step.x, step.y), None
            else:
                result = self.android.find_with_confidence(
                    text=step.text, id=step.id, desc=step.desc, min_confidence=step.min_confidence
                )
                if result and result.confidence >= step.min_confidence:
                    success = self.android.tap(
                        step.text,
                        id=step.id,
                        desc=step.desc,
                        timeout=step.timeout,
                        min_confidence=step.min_confidence,
                    )
                    return success, result.confidence
                return False, result.confidence if result else 0.0

        elif action == "long_press":
            duration = int(step.timeout * 1000) if step.timeout > 1 else 1000
            if step.x is not None and step.y is not None:
                return self.android.long_press(step.x, step.y, duration_ms=duration), None
            else:
                return (
                    self.android.long_press(
                        step.text,
                        id=step.id,
                        desc=step.desc,
                        timeout=step.timeout,
                        min_confidence=step.min_confidence,
                    ),
                    None,
                )

        elif action == "swipe":
            direction = step.direction or "up"
            return self.android.swipe(direction), None

        elif action == "scroll":
            direction = step.direction or "down"
            return self.android.scroll(direction), None

        elif action == "type":
            if step.value:
                return self.android.type(step.value), None
            return False, None

        elif action == "press":
            key = step.value or "back"
            key_map = {
                "back": "press_back",
                "home": "press_home",
                "enter": "press_enter",
            }
            if key in key_map:
                return getattr(self.android, key_map[key])(), None
            else:
                return self.android.press_key(key), None

        elif action == "open":
            if step.app:
                return self.android.open_app(step.app), None
            return False, None

        elif action == "wait":
            time.sleep(step.timeout)
            return True, None

        elif action == "wait_for":
            result = self.android.wait_for_with_confidence(
                text=step.text,
                id=step.id,
                desc=step.desc,
                timeout=step.timeout,
                min_confidence=step.min_confidence,
            )
            if result:
                return True, result.confidence
            return False, None

        elif action == "assert_exists":
            result = self.android.find_with_confidence(
                text=step.text, id=step.id, desc=step.desc, min_confidence=step.min_confidence
            )
            if result and result.confidence >= step.min_confidence:
                return True, result.confidence
            return False, result.confidence if result else 0.0

        elif action == "assert_not_exists":
            result = self.android.find_with_confidence(
                text=step.text, id=step.id, desc=step.desc, min_confidence=step.min_confidence
            )
            if result is None or result.confidence < step.min_confidence:
                return True, None
            return False, result.confidence

        elif action == "screenshot":
            filename = step.value or None
            try:
                self.android.screenshot(filename)
                return True, None
            except Exception:
                return False, None

        # Variable operations
        elif action == "set_variable":
            return self._do_set_variable(step)

        elif action == "extract":
            return self._do_extract(step)

        # Control flow
        elif action == "if":
            return self._do_if(step)

        elif action == "for":
            return self._do_for(step)

        elif action == "while":
            return self._do_while(step)

        elif action == "until":
            return self._do_until(step)

        elif action == "break":
            return self._do_break(step)

        elif action == "continue":
            return self._do_continue(step)

        # Utility
        elif action == "log":
            return self._do_log(step)

        elif action == "assert":
            return self._do_assert(step)

        else:
            logger.warning(f"Unknown action: {action}")
            return False, None

    def _do_set_variable(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute set_variable action."""
        if not step.variable:
            logger.error("set_variable requires 'variable' field")
            return False, None

        try:
            if step.expr:
                # Evaluate expression
                result = self._expr_engine.evaluate(step.expr)
                if result.success:
                    self._context.set(step.variable, result.value)
                    logger.debug(f"Set variable '{step.variable}' = {result.value}")
                    return True, None
                else:
                    logger.error(f"Expression evaluation failed: {result.error}")
                    return False, None
            elif step.value is not None:
                # Direct value assignment
                self._context.set(step.variable, step.value)
                logger.debug(f"Set variable '{step.variable}' = {step.value}")
                return True, None
            else:
                logger.error("set_variable requires 'expr' or 'value' field")
                return False, None
        except Exception as e:
            logger.error(f"Failed to set variable: {e}")
            return False, None

    def _do_extract(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute extract action - extract data from UI element."""
        if not step.variable:
            logger.error("extract requires 'variable' field")
            return False, None

        try:
            # Find the element
            result = self.android.find_with_confidence(
                text=step.text, id=step.id, desc=step.desc, min_confidence=step.min_confidence
            )

            if not result or not result.element:
                logger.warning("Element not found for extract")
                return False, result.confidence if result else 0.0

            element = result.element
            source = step.extract_source or "text"
            extracted_value = None

            if source == "text":
                extracted_value = element.get("text", "")
            elif source == "attribute":
                attr_name = step.extract_attr or "text"
                extracted_value = element.get(attr_name, "")
            elif source == "bounds":
                extracted_value = element.get("bounds", (0, 0, 0, 0))
            elif source == "resource_id":
                extracted_value = element.get("resource_id", "")
            elif source == "content_desc":
                extracted_value = element.get("content_desc", "")
            elif source == "class":
                extracted_value = element.get("class", "")
            else:
                extracted_value = element.get(source, "")

            # Apply regex if specified
            if step.regex and isinstance(extracted_value, str):
                match = re.search(step.regex, extracted_value)
                if match:
                    # Use first group if available, otherwise full match
                    extracted_value = match.group(1) if match.groups() else match.group(0)
                else:
                    logger.warning(f"Regex pattern did not match: {step.regex}")
                    extracted_value = None

            if extracted_value is not None:
                self._context.set(step.variable, extracted_value)
                logger.debug(f"Extracted '{step.variable}' = {extracted_value}")
                return True, result.confidence

            return False, result.confidence

        except Exception as e:
            logger.error(f"Failed to extract: {e}")
            return False, None

    def _do_if(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute if action with conditional branching."""
        from core.control_flow import IfBlock

        # Build condition from step
        condition = step.expr or ""

        # Parse then/else/elif steps
        then_steps = []
        if step.then_steps:
            then_steps = [Step(**s) if isinstance(s, dict) else s for s in step.then_steps]

        else_steps = []
        if step.else_steps:
            else_steps = [Step(**s) if isinstance(s, dict) else s for s in step.else_steps]

        elif_blocks = []
        if step.elif_blocks:
            for elif_data in step.elif_blocks:
                elif_cond = elif_data.get("condition", elif_data.get("expr", ""))
                elif_step_data = elif_data.get("steps", elif_data.get("then_steps", []))
                elif_step_list = [Step(**s) if isinstance(s, dict) else s for s in elif_step_data]
                elif_blocks.append((elif_cond, elif_step_list))

        if_block = IfBlock(
            condition=condition,
            then_steps=then_steps,
            elif_blocks=elif_blocks,
            else_steps=else_steps,
        )

        try:
            results = self._control_flow.execute_if(if_block)
            # If any step in the branch failed, this fails
            for r in results:
                if r.status == StepStatus.FAILED:
                    return False, None
            return True, None
        except (BreakException, ContinueException):
            # Let break/continue propagate up to enclosing loop
            raise
        except Exception as e:
            logger.error(f"If execution failed: {e}")
            return False, None

    def _do_for(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute for loop action."""
        from core.control_flow import ForBlock

        # Parse loop steps
        loop_steps = []
        steps_data = step.loop_steps or step.then_steps or []
        for s in steps_data:
            if isinstance(s, dict):
                loop_steps.append(Step(**s))
            else:
                loop_steps.append(s)

        for_block = ForBlock(
            items=step.items or "[]",
            item_var=step.item_var or "item",
            index_var=step.index_var,
            steps=loop_steps,
            max_iterations=step.max_iterations,
        )

        self._in_loop = True
        self._loop_depth += 1

        try:
            results = self._control_flow.execute_for(for_block)
            for r in results:
                if r.status == StepStatus.FAILED:
                    return False, None
            return True, None
        except LoopLimitError as e:
            logger.error(f"For loop exceeded max iterations: {e}")
            return False, None
        except Exception as e:
            logger.error(f"For loop execution failed: {e}")
            return False, None
        finally:
            self._loop_depth -= 1
            if self._loop_depth == 0:
                self._in_loop = False

    def _do_while(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute while loop action."""
        from core.control_flow import WhileBlock

        # Parse loop steps
        loop_steps = []
        steps_data = step.loop_steps or step.then_steps or []
        for s in steps_data:
            if isinstance(s, dict):
                loop_steps.append(Step(**s))
            else:
                loop_steps.append(s)

        while_block = WhileBlock(
            condition=step.expr or "False",
            steps=loop_steps,
            max_iterations=step.max_iterations,
            counter_var=step.counter_var,
        )

        self._in_loop = True
        self._loop_depth += 1

        try:
            results = self._control_flow.execute_while(while_block)
            for r in results:
                if r.status == StepStatus.FAILED:
                    return False, None
            return True, None
        except LoopLimitError as e:
            logger.error(f"While loop exceeded max iterations: {e}")
            return False, None
        except Exception as e:
            logger.error(f"While loop execution failed: {e}")
            return False, None
        finally:
            self._loop_depth -= 1
            if self._loop_depth == 0:
                self._in_loop = False

    def _do_until(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute until loop action."""
        from core.control_flow import UntilBlock

        # Parse loop steps
        loop_steps = []
        steps_data = step.loop_steps or step.then_steps or []
        for s in steps_data:
            if isinstance(s, dict):
                loop_steps.append(Step(**s))
            else:
                loop_steps.append(s)

        until_block = UntilBlock(
            condition=step.expr or "True",
            steps=loop_steps,
            max_iterations=step.max_iterations,
            counter_var=step.counter_var,
        )

        self._in_loop = True
        self._loop_depth += 1

        try:
            results = self._control_flow.execute_until(until_block)
            for r in results:
                if r.status == StepStatus.FAILED:
                    return False, None
            return True, None
        except LoopLimitError as e:
            logger.error(f"Until loop exceeded max iterations: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Until loop execution failed: {e}")
            return False, None
        finally:
            self._loop_depth -= 1
            if self._loop_depth == 0:
                self._in_loop = False

    def _do_break(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute break action."""
        if not self._in_loop:
            raise InvalidControlFlowError("break")
        raise BreakException()

    def _do_continue(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute continue action."""
        if not self._in_loop:
            raise InvalidControlFlowError("continue")
        raise ContinueException()

    def _do_log(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute log action."""
        message = step.message or step.value or ""

        # Resolve any remaining variables in message
        if self._resolver.has_variables(message):
            message = self._resolver.resolve_string(message)

        level = step.level.lower()
        if level == "debug":
            logger.debug(f"[LOG] {message}")
        elif level == "warning":
            logger.warning(f"[LOG] {message}")
        elif level == "error":
            logger.error(f"[LOG] {message}")
        else:
            logger.info(f"[LOG] {message}")

        return True, None

    def _do_assert(self, step: Step) -> Tuple[bool, Optional[float]]:
        """Execute assert action."""
        condition = step.expr or ""
        message = step.message or f"Assertion: {condition}"

        result = self._expr_engine.evaluate_bool(condition)

        if result:
            logger.debug(f"Assertion passed: {condition}")
            return True, None
        else:
            logger.error(f"Assertion failed: {condition} - {message}")
            raise AssertionFailedError(condition, message)

    @property
    def context(self) -> "VariableContext":
        """Get the variable context."""
        return self._context

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable in the context."""
        self._context.set(name, value)

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable from the context."""
        return self._context.get(name, default)

    def run_from_file(
        self, filepath: Union[str, Path], extra_vars: Optional[Dict[str, Any]] = None
    ) -> AutomationResult:
        """
        Load and run automation from JSON file.

        Args:
            filepath: Path to JSON file with steps
            extra_vars: Additional variables to set (overrides file variables)

        Returns:
            AutomationResult
        """
        filepath = Path(filepath)

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        # Load variables from file if present
        initial_vars = {}
        if isinstance(data, dict):
            file_vars = data.get("variables", {})
            if isinstance(file_vars, dict):
                initial_vars.update(file_vars)

        # Extra vars override file vars
        if extra_vars:
            initial_vars.update(extra_vars)

        steps_data = data.get("steps", data) if isinstance(data, dict) else data
        steps = [Step(**s) for s in steps_data]

        return self.run(steps, initial_vars=initial_vars)

    def save_result(self, result: AutomationResult, filepath: Union[str, Path]) -> None:
        """Save automation result to JSON file."""
        filepath = Path(filepath)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Result saved to {filepath}")


# Convenience functions for simple usage
def run_steps(steps: List[Step], **kwargs) -> AutomationResult:
    """Run automation steps with default settings."""
    auto = Automation(**kwargs)
    return auto.run(steps)


def tap(text: Optional[str] = None, **kwargs) -> Step:
    """Create a tap step."""
    return Step(action="tap", text=text, **kwargs)


def wait(seconds: float) -> Step:
    """Create a wait step."""
    return Step(action="wait", timeout=seconds)


def wait_for(text: Optional[str] = None, timeout: float = 10.0, **kwargs) -> Step:
    """Create a wait_for step."""
    return Step(action="wait_for", text=text, timeout=timeout, **kwargs)


def type_text(value: str, **kwargs) -> Step:
    """Create a type step."""
    return Step(action="type", value=value, **kwargs)


def swipe(direction: str, **kwargs) -> Step:
    """Create a swipe step."""
    return Step(action="swipe", direction=direction, **kwargs)


def open_app(name: str, **kwargs) -> Step:
    """Create an open app step."""
    return Step(action="open", app=name, **kwargs)


def press(key: str, **kwargs) -> Step:
    """Create a press key step."""
    return Step(action="press", value=key, **kwargs)
