"""
Unit tests for core.control_flow module.

Tests ControlFlowExecutor for:
- If/elif/else execution
- For loop execution
- While loop execution
- Until loop execution
- Break and continue handling
- Loop limit enforcement
"""

from typing import List

import pytest

from core.automation import Step, StepResult, StepStatus
from core.control_flow import (
    ControlFlowExecutor,
    ForBlock,
    IfBlock,
    UntilBlock,
    WhileBlock,
    parse_for_block,
    parse_if_block,
    parse_until_block,
    parse_while_block,
)
from core.exceptions import (
    BreakException,
    ContinueException,
    InvalidControlFlowError,
    LoopLimitError,
)
from core.expressions import SafeExpressionEngine
from core.variables import VariableContext


class MockStepResult:
    """Create a mock step result for testing."""

    @staticmethod
    def success(index: int = 0, step_type: str = "test") -> StepResult:
        return StepResult(
            step_index=index, step_type=step_type, status=StepStatus.SUCCESS, message="Test step"
        )

    @staticmethod
    def failed(index: int = 0, step_type: str = "test") -> StepResult:
        return StepResult(
            step_index=index,
            step_type=step_type,
            status=StepStatus.FAILED,
            message="Test step",
            error="Step failed",
        )


class TestIfBlock:
    """Tests for if/elif/else execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"x": 10, "flag": True})
        self.engine = SafeExpressionEngine(self.ctx)
        self.executed_steps = []

        def mock_executor(steps: List[Step]) -> List[StepResult]:
            self.executed_steps.extend(steps)
            return [MockStepResult.success(i) for i in range(len(steps))]

        self.executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

    def test_if_true(self):
        """Test if block with true condition."""
        then_step = Step(action="log", message="then branch")
        else_step = Step(action="log", message="else branch")

        if_block = IfBlock(condition="x > 5", then_steps=[then_step], else_steps=[else_step])

        self.executor.execute_if(if_block)

        assert len(self.executed_steps) == 1
        assert self.executed_steps[0].message == "then branch"

    def test_if_false(self):
        """Test if block with false condition."""
        then_step = Step(action="log", message="then branch")
        else_step = Step(action="log", message="else branch")

        if_block = IfBlock(condition="x < 5", then_steps=[then_step], else_steps=[else_step])

        self.executor.execute_if(if_block)

        assert len(self.executed_steps) == 1
        assert self.executed_steps[0].message == "else branch"

    def test_if_no_else(self):
        """Test if block without else."""
        then_step = Step(action="log", message="then branch")

        if_block = IfBlock(condition="x < 5", then_steps=[then_step])

        results = self.executor.execute_if(if_block)

        assert len(self.executed_steps) == 0
        assert len(results) == 0

    def test_elif(self):
        """Test elif clause."""
        then_step = Step(action="log", message="then")
        elif_step = Step(action="log", message="elif")
        else_step = Step(action="log", message="else")

        if_block = IfBlock(
            condition="x > 20",  # False
            then_steps=[then_step],
            elif_blocks=[
                ("x > 5", [elif_step]),  # True
            ],
            else_steps=[else_step],
        )

        self.executor.execute_if(if_block)

        assert len(self.executed_steps) == 1
        assert self.executed_steps[0].message == "elif"

    def test_multiple_elif(self):
        """Test multiple elif clauses."""
        self.ctx.set("value", 50)

        if_block = IfBlock(
            condition="value > 100",
            then_steps=[Step(action="log", message="over 100")],
            elif_blocks=[
                ("value > 75", [Step(action="log", message="over 75")]),
                ("value > 25", [Step(action="log", message="over 25")]),
            ],
            else_steps=[Step(action="log", message="25 or under")],
        )

        self.executor.execute_if(if_block)

        assert len(self.executed_steps) == 1
        assert self.executed_steps[0].message == "over 25"


class TestForBlock:
    """Tests for for loop execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"items": ["a", "b", "c"]})
        self.engine = SafeExpressionEngine(self.ctx)
        self.executed_steps = []
        self.iteration_values = []

        def mock_executor(steps: List[Step]) -> List[StepResult]:
            # Capture the current item value
            if self.ctx.has("item"):
                self.iteration_values.append(self.ctx.get("item"))
            self.executed_steps.extend(steps)
            return [MockStepResult.success(i) for i in range(len(steps))]

        self.executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

    def test_for_basic(self):
        """Test basic for loop."""
        for_block = ForBlock(
            items="items",
            item_var="item",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
        )

        self.executor.execute_for(for_block)

        assert len(self.executed_steps) == 3
        assert self.iteration_values == ["a", "b", "c"]

    def test_for_with_index(self):
        """Test for loop with index variable."""
        index_values = []

        def mock_executor(steps: List[Step]) -> List[StepResult]:
            if self.ctx.has("i"):
                index_values.append(self.ctx.get("i"))
            return [MockStepResult.success()]

        executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

        for_block = ForBlock(
            items="items",
            item_var="item",
            index_var="i",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
        )

        executor.execute_for(for_block)

        assert index_values == [0, 1, 2]

    def test_for_inline_list(self):
        """Test for loop with inline list."""
        for_block = ForBlock(
            items="[1, 2, 3]",
            item_var="num",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
        )

        self.executor.execute_for(for_block)

        assert len(self.executed_steps) == 3

    def test_for_max_iterations(self):
        """Test for loop max iterations limit."""
        for_block = ForBlock(
            items="range(1000)",
            item_var="i",
            steps=[Step(action="log", message="iteration")],
            max_iterations=10,
        )

        with pytest.raises(LoopLimitError):
            self.executor.execute_for(for_block)

    def test_for_cleanup(self):
        """Test that loop variables are cleaned up after loop."""
        for_block = ForBlock(
            items="[1]",
            item_var="temp_item",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
        )

        self.executor.execute_for(for_block)

        assert not self.ctx.has("temp_item")


class TestWhileBlock:
    """Tests for while loop execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"counter": 0})
        self.engine = SafeExpressionEngine(self.ctx)
        self.executed_steps = []

        def mock_executor(steps: List[Step]) -> List[StepResult]:
            # Increment counter on each iteration
            self.ctx.set("counter", self.ctx.get("counter") + 1)
            self.executed_steps.extend(steps)
            return [MockStepResult.success()]

        self.executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

    def test_while_basic(self):
        """Test basic while loop."""
        while_block = WhileBlock(
            condition="counter < 3",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
        )

        self.executor.execute_while(while_block)

        assert len(self.executed_steps) == 3
        assert self.ctx.get("counter") == 3

    def test_while_false_condition(self):
        """Test while loop with initially false condition."""
        self.ctx.set("counter", 10)

        while_block = WhileBlock(
            condition="counter < 3",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
        )

        self.executor.execute_while(while_block)

        assert len(self.executed_steps) == 0

    def test_while_max_iterations(self):
        """Test while loop max iterations limit."""
        # Counter will keep incrementing but condition always true
        self.ctx.set("always_true", True)

        while_block = WhileBlock(
            condition="always_true",
            steps=[Step(action="log", message="iteration")],
            max_iterations=5,
        )

        with pytest.raises(LoopLimitError):
            self.executor.execute_while(while_block)

    def test_while_counter_var(self):
        """Test while loop with counter variable."""
        counter_values = []

        def mock_executor(steps: List[Step]) -> List[StepResult]:
            if self.ctx.has("iter_count"):
                counter_values.append(self.ctx.get("iter_count"))
            self.ctx.set("counter", self.ctx.get("counter") + 1)
            return [MockStepResult.success()]

        executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

        while_block = WhileBlock(
            condition="counter < 3",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
            counter_var="iter_count",
        )

        executor.execute_while(while_block)

        assert counter_values == [1, 2, 3]


class TestUntilBlock:
    """Tests for until loop execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext({"counter": 0})
        self.engine = SafeExpressionEngine(self.ctx)
        self.executed_steps = []

        def mock_executor(steps: List[Step]) -> List[StepResult]:
            self.ctx.set("counter", self.ctx.get("counter") + 1)
            self.executed_steps.extend(steps)
            return [MockStepResult.success()]

        self.executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

    def test_until_basic(self):
        """Test basic until loop (loops until condition is true)."""
        until_block = UntilBlock(
            condition="counter >= 3",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
        )

        self.executor.execute_until(until_block)

        assert len(self.executed_steps) == 3
        assert self.ctx.get("counter") == 3

    def test_until_true_condition(self):
        """Test until loop with initially true condition."""
        self.ctx.set("done", True)

        until_block = UntilBlock(
            condition="done", steps=[Step(action="log", message="iteration")], max_iterations=100
        )

        self.executor.execute_until(until_block)

        # Should run once then stop
        assert len(self.executed_steps) == 1

    def test_until_max_iterations(self):
        """Test until loop max iterations limit."""
        # Condition never becomes true
        until_block = UntilBlock(
            condition="counter > 1000",
            steps=[Step(action="log", message="iteration")],
            max_iterations=5,
        )

        with pytest.raises(LoopLimitError):
            self.executor.execute_until(until_block)


class TestBreakContinue:
    """Tests for break and continue handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = VariableContext()
        self.engine = SafeExpressionEngine(self.ctx)

    def test_break_outside_loop(self):
        """Test break outside of loop raises error."""

        def mock_executor(steps):
            return []

        executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

        with pytest.raises(InvalidControlFlowError) as exc_info:
            executor.handle_break()

        assert "break" in str(exc_info.value)

    def test_continue_outside_loop(self):
        """Test continue outside of loop raises error."""

        def mock_executor(steps):
            return []

        executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

        with pytest.raises(InvalidControlFlowError) as exc_info:
            executor.handle_continue()

        assert "continue" in str(exc_info.value)

    def test_break_in_loop(self):
        """Test break inside loop."""
        iteration_count = [0]

        def mock_executor(steps: List[Step]) -> List[StepResult]:
            iteration_count[0] += 1
            if iteration_count[0] >= 2:
                raise BreakException()
            return [MockStepResult.success()]

        executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

        for_block = ForBlock(
            items="[1, 2, 3, 4, 5]",
            item_var="i",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
        )

        executor.execute_for(for_block)

        assert iteration_count[0] == 2

    def test_continue_in_loop(self):
        """Test continue inside loop."""
        iteration_count = [0]
        processed = []

        def mock_executor(steps: List[Step]) -> List[StepResult]:
            iteration_count[0] += 1
            current = self.ctx.get("i")
            if current == 2:
                raise ContinueException()
            processed.append(current)
            return [MockStepResult.success()]

        executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)
        self.ctx.set("items", [1, 2, 3])

        for_block = ForBlock(
            items="items",
            item_var="i",
            steps=[Step(action="log", message="iteration")],
            max_iterations=100,
        )

        executor.execute_for(for_block)

        assert iteration_count[0] == 3
        assert processed == [1, 3]  # 2 was skipped

    def test_loop_depth(self):
        """Test loop depth tracking."""

        def mock_executor(steps):
            return []

        executor = ControlFlowExecutor(self.engine, self.ctx, mock_executor)

        assert executor.loop_depth == 0
        assert executor.in_loop is False


class TestParseBlocks:
    """Tests for block parsing functions."""

    def test_parse_if_block(self):
        """Test parsing if block from dict."""
        data = {
            "action": "if",
            "condition": "x > 5",
            "then": [{"action": "log", "message": "then"}],
            "else": [{"action": "log", "message": "else"}],
        }

        # Note: parse_if_block expects 'condition' in step data for expr
        # and uses 'then' key directly
        if_block = parse_if_block(data)

        assert if_block.condition == "x > 5"
        assert len(if_block.then_steps) == 1
        assert len(if_block.else_steps) == 1

    def test_parse_for_block(self):
        """Test parsing for block from dict."""
        data = {
            "action": "for",
            "items": "[1, 2, 3]",
            "item_var": "num",
            "steps": [{"action": "log", "message": "iteration"}],
            "max_iterations": 50,
        }

        for_block = parse_for_block(data)

        assert for_block.items == "[1, 2, 3]"
        assert for_block.item_var == "num"
        assert len(for_block.steps) == 1
        assert for_block.max_iterations == 50

    def test_parse_while_block(self):
        """Test parsing while block from dict."""
        data = {
            "action": "while",
            "condition": "counter < 10",
            "steps": [{"action": "log", "message": "loop"}],
            "counter_var": "i",
        }

        while_block = parse_while_block(data)

        assert while_block.condition == "counter < 10"
        assert while_block.counter_var == "i"
        assert len(while_block.steps) == 1

    def test_parse_until_block(self):
        """Test parsing until block from dict."""
        data = {
            "action": "until",
            "condition": "done == True",
            "steps": [{"action": "log", "message": "waiting"}],
            "max_iterations": 20,
        }

        until_block = parse_until_block(data)

        assert until_block.condition == "done == True"
        assert until_block.max_iterations == 20
        assert len(until_block.steps) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
