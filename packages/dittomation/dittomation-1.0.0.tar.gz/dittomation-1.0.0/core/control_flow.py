"""
Control Flow Execution for DittoMation automation.

Provides control flow constructs: if/else, for loops, while loops, until loops.
Integrates with the expression engine for condition evaluation.

Usage:
    from core.control_flow import ControlFlowExecutor

    # Create executor with expression engine
    executor = ControlFlowExecutor(expr_engine, step_executor)

    # Execute if block
    results = executor.execute_if(if_block)

    # Execute for loop
    results = executor.execute_for(for_block)
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from core.exceptions import (
    BreakException,
    ContinueException,
    InvalidControlFlowError,
    LoopLimitError,
)
from core.logging_config import get_logger

if TYPE_CHECKING:
    from core.automation import Step, StepResult
    from core.expressions import SafeExpressionEngine
    from core.variables import VariableContext


logger = get_logger("control_flow")


@dataclass
class IfBlock:
    """
    Represents an if/elif/else block.

    Attributes:
        condition: Expression string for the if condition
        then_steps: Steps to execute if condition is True
        elif_blocks: List of (condition, steps) tuples for elif clauses
        else_steps: Steps to execute if all conditions are False
    """

    condition: str
    then_steps: List["Step"] = field(default_factory=list)
    elif_blocks: List[Tuple[str, List["Step"]]] = field(default_factory=list)
    else_steps: List["Step"] = field(default_factory=list)


@dataclass
class ForBlock:
    """
    Represents a for loop block.

    Attributes:
        items: Expression that evaluates to an iterable
        item_var: Variable name to store current item
        index_var: Optional variable name to store current index
        steps: Steps to execute for each item
        max_iterations: Maximum iterations before raising LoopLimitError
    """

    items: str
    item_var: str
    steps: List["Step"] = field(default_factory=list)
    index_var: Optional[str] = None
    max_iterations: int = 100


@dataclass
class WhileBlock:
    """
    Represents a while loop block.

    Attributes:
        condition: Expression that determines loop continuation
        steps: Steps to execute each iteration
        max_iterations: Maximum iterations before raising LoopLimitError
        counter_var: Optional variable name to store iteration count
    """

    condition: str
    steps: List["Step"] = field(default_factory=list)
    max_iterations: int = 100
    counter_var: Optional[str] = None


@dataclass
class UntilBlock:
    """
    Represents an until loop block (loops until condition becomes True).

    Attributes:
        condition: Expression that stops the loop when True
        steps: Steps to execute each iteration
        max_iterations: Maximum iterations before raising LoopLimitError
        counter_var: Optional variable name to store iteration count
    """

    condition: str
    steps: List["Step"] = field(default_factory=list)
    max_iterations: int = 100
    counter_var: Optional[str] = None


class ControlFlowExecutor:
    """
    Executes control flow constructs.

    Integrates with:
    - SafeExpressionEngine for condition evaluation
    - VariableContext for loop variables
    - Step executor callback for running steps

    Example:
        def execute_steps(steps):
            # Execute steps and return results
            return [...]

        executor = ControlFlowExecutor(expr_engine, context, execute_steps)
        results = executor.execute_if(if_block)
    """

    def __init__(
        self,
        expr_engine: "SafeExpressionEngine",
        context: "VariableContext",
        step_executor: Callable[[List["Step"]], List["StepResult"]],
    ):
        """
        Initialize control flow executor.

        Args:
            expr_engine: Expression engine for condition evaluation
            context: Variable context for loop variables
            step_executor: Callback to execute steps, returns list of StepResults
        """
        self.expr_engine = expr_engine
        self.context = context
        self.step_executor = step_executor
        self._in_loop = False
        self._loop_depth = 0

    def execute_if(self, if_block: IfBlock) -> List["StepResult"]:
        """
        Execute an if/elif/else block.

        Args:
            if_block: IfBlock with conditions and steps

        Returns:
            List of StepResults from executed branch
        """
        # Check main condition
        if self.expr_engine.evaluate_bool(if_block.condition):
            logger.debug(f"If condition '{if_block.condition}' is True, executing then_steps")
            return self.step_executor(if_block.then_steps)

        # Check elif conditions
        for elif_cond, elif_steps in if_block.elif_blocks:
            if self.expr_engine.evaluate_bool(elif_cond):
                logger.debug(f"Elif condition '{elif_cond}' is True, executing elif_steps")
                return self.step_executor(elif_steps)

        # Execute else if present
        if if_block.else_steps:
            logger.debug("All conditions False, executing else_steps")
            return self.step_executor(if_block.else_steps)

        logger.debug("All conditions False and no else block")
        return []

    def execute_for(self, for_block: ForBlock) -> List["StepResult"]:
        """
        Execute a for loop.

        Args:
            for_block: ForBlock with items expression and steps

        Returns:
            List of all StepResults from all iterations
        """
        # Evaluate items expression
        result = self.expr_engine.evaluate(for_block.items)
        if not result.success:
            raise ValueError(f"Failed to evaluate items expression: {result.error}")

        items = result.value
        if not hasattr(items, "__iter__"):
            raise ValueError(f"Items expression must be iterable, got: {type(items).__name__}")

        items = list(items)
        all_results: List[StepResult] = []

        # Check max iterations
        if len(items) > for_block.max_iterations:
            raise LoopLimitError("for", for_block.max_iterations, for_block.items)

        self._loop_depth += 1
        self._in_loop = True

        try:
            for i, item in enumerate(items):
                # Set loop variables
                self.context.set(for_block.item_var, item)
                if for_block.index_var:
                    self.context.set(for_block.index_var, i)

                logger.debug(f"For loop iteration {i+1}/{len(items)}: {for_block.item_var}={item}")

                try:
                    results = self.step_executor(for_block.steps)
                    all_results.extend(results)
                except BreakException:
                    logger.debug("Break encountered, exiting for loop")
                    break
                except ContinueException:
                    logger.debug("Continue encountered, moving to next iteration")
                    continue

        finally:
            self._loop_depth -= 1
            if self._loop_depth == 0:
                self._in_loop = False
            # Clean up loop variables
            self.context.delete(for_block.item_var)
            if for_block.index_var:
                self.context.delete(for_block.index_var)

        return all_results

    def execute_while(self, while_block: WhileBlock) -> List["StepResult"]:
        """
        Execute a while loop.

        Args:
            while_block: WhileBlock with condition and steps

        Returns:
            List of all StepResults from all iterations
        """
        all_results: List[StepResult] = []
        iteration = 0

        self._loop_depth += 1
        self._in_loop = True

        try:
            while self.expr_engine.evaluate_bool(while_block.condition):
                iteration += 1

                if iteration > while_block.max_iterations:
                    raise LoopLimitError("while", while_block.max_iterations, while_block.condition)

                # Set counter variable if specified
                if while_block.counter_var:
                    self.context.set(while_block.counter_var, iteration)

                logger.debug(
                    f"While loop iteration {iteration}: condition '{while_block.condition}'"
                )

                try:
                    results = self.step_executor(while_block.steps)
                    all_results.extend(results)
                except BreakException:
                    logger.debug("Break encountered, exiting while loop")
                    break
                except ContinueException:
                    logger.debug("Continue encountered, re-checking condition")
                    continue

        finally:
            self._loop_depth -= 1
            if self._loop_depth == 0:
                self._in_loop = False
            # Clean up counter variable
            if while_block.counter_var:
                self.context.delete(while_block.counter_var)

        return all_results

    def execute_until(self, until_block: UntilBlock) -> List["StepResult"]:
        """
        Execute an until loop (loops until condition becomes True).

        Args:
            until_block: UntilBlock with condition and steps

        Returns:
            List of all StepResults from all iterations
        """
        all_results: List[StepResult] = []
        iteration = 0

        self._loop_depth += 1
        self._in_loop = True

        try:
            while True:
                iteration += 1

                if iteration > until_block.max_iterations:
                    raise LoopLimitError("until", until_block.max_iterations, until_block.condition)

                # Set counter variable if specified
                if until_block.counter_var:
                    self.context.set(until_block.counter_var, iteration)

                logger.debug(
                    f"Until loop iteration {iteration}: condition '{until_block.condition}'"
                )

                try:
                    results = self.step_executor(until_block.steps)
                    all_results.extend(results)
                except BreakException:
                    logger.debug("Break encountered, exiting until loop")
                    break
                except ContinueException:
                    logger.debug("Continue encountered, re-checking condition")
                    # Check condition after continue
                    if self.expr_engine.evaluate_bool(until_block.condition):
                        break
                    continue

                # Check termination condition after steps
                if self.expr_engine.evaluate_bool(until_block.condition):
                    logger.debug(
                        f"Until condition '{until_block.condition}' became True, exiting loop"
                    )
                    break

        finally:
            self._loop_depth -= 1
            if self._loop_depth == 0:
                self._in_loop = False
            # Clean up counter variable
            if until_block.counter_var:
                self.context.delete(until_block.counter_var)

        return all_results

    def handle_break(self) -> None:
        """
        Handle a break statement.

        Raises:
            InvalidControlFlowError: If not inside a loop
            BreakException: To signal loop exit
        """
        if not self._in_loop:
            raise InvalidControlFlowError("break")
        raise BreakException()

    def handle_continue(self) -> None:
        """
        Handle a continue statement.

        Raises:
            InvalidControlFlowError: If not inside a loop
            ContinueException: To signal continue to next iteration
        """
        if not self._in_loop:
            raise InvalidControlFlowError("continue")
        raise ContinueException()

    @property
    def in_loop(self) -> bool:
        """Check if currently executing inside a loop."""
        return self._in_loop

    @property
    def loop_depth(self) -> int:
        """Get current loop nesting depth."""
        return self._loop_depth


def parse_if_block(step_data: Dict[str, Any]) -> IfBlock:
    """
    Parse an if block from step data.

    Expected format:
    {
        "action": "if",
        "condition": "count > 5",
        "then": [...steps...],
        "elif": [
            {"condition": "count > 3", "steps": [...]}
        ],
        "else": [...steps...]
    }
    """
    from core.automation import Step

    condition = step_data.get("condition", "")
    then_steps = [Step(**s) for s in step_data.get("then", step_data.get("then_steps", []))]

    elif_blocks = []
    for elif_data in step_data.get("elif", step_data.get("elif_blocks", [])):
        elif_cond = elif_data.get("condition", "")
        elif_steps = [Step(**s) for s in elif_data.get("steps", [])]
        elif_blocks.append((elif_cond, elif_steps))

    else_steps = [Step(**s) for s in step_data.get("else", step_data.get("else_steps", []))]

    return IfBlock(
        condition=condition, then_steps=then_steps, elif_blocks=elif_blocks, else_steps=else_steps
    )


def parse_for_block(step_data: Dict[str, Any]) -> ForBlock:
    """
    Parse a for block from step data.

    Expected format:
    {
        "action": "for",
        "items": "['a', 'b', 'c']",
        "item_var": "item",
        "index_var": "i",
        "steps": [...steps...],
        "max_iterations": 100
    }
    """
    from core.automation import Step

    return ForBlock(
        items=step_data.get("items", "[]"),
        item_var=step_data.get("item_var", "item"),
        index_var=step_data.get("index_var"),
        steps=[Step(**s) for s in step_data.get("steps", step_data.get("loop_steps", []))],
        max_iterations=step_data.get("max_iterations", 100),
    )


def parse_while_block(step_data: Dict[str, Any]) -> WhileBlock:
    """
    Parse a while block from step data.

    Expected format:
    {
        "action": "while",
        "condition": "count < 10",
        "steps": [...steps...],
        "max_iterations": 100,
        "counter_var": "iteration"
    }
    """
    from core.automation import Step

    return WhileBlock(
        condition=step_data.get("condition", "False"),
        steps=[Step(**s) for s in step_data.get("steps", step_data.get("loop_steps", []))],
        max_iterations=step_data.get("max_iterations", 100),
        counter_var=step_data.get("counter_var"),
    )


def parse_until_block(step_data: Dict[str, Any]) -> UntilBlock:
    """
    Parse an until block from step data.

    Expected format:
    {
        "action": "until",
        "condition": "element_exists(text='Success')",
        "steps": [...steps...],
        "max_iterations": 100,
        "counter_var": "attempt"
    }
    """
    from core.automation import Step

    return UntilBlock(
        condition=step_data.get("condition", "True"),
        steps=[Step(**s) for s in step_data.get("steps", step_data.get("loop_steps", []))],
        max_iterations=step_data.get("max_iterations", 100),
        counter_var=step_data.get("counter_var"),
    )
