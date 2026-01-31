import json
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mistralai_workflows.exceptions import ErrorCode, WorkflowsException
from pydantic import BaseModel, Field

from mistralai_workflows.plugins.agents.tool import execute_activity_tool


@pytest.fixture
def mock_tool_execution() -> Generator[tuple[MagicMock | AsyncMock, MagicMock | AsyncMock], Any, None]:
    """Mock tool execution dependencies to isolate execute_activity_tool testing."""
    with (
        patch("mistralai_workflows.plugins.agents.tool.get_wrapped_activity") as mock_activity,
        patch("mistralai_workflows.plugins.agents.tool.get_function_signature_type_hints") as mock_hints,
    ):
        yield mock_activity, mock_hints


class TestExecuteActivityTool:
    @pytest.mark.asyncio
    async def test_execute_activity_tool_invalid_json(
        self, mock_tool_execution: tuple[MagicMock | AsyncMock, MagicMock | AsyncMock]
    ) -> None:
        async def mock_activity() -> None:
            return None

        mock_activity_fn, mock_hints = mock_tool_execution
        mock_activity_fn.return_value = mock_activity
        mock_hints.return_value = ({}, None)

        with pytest.raises(WorkflowsException, match="Invalid arguments for tool"):
            await execute_activity_tool("mock_activity", "{invalid json}", raise_on_tool_fail=True)

        result = await execute_activity_tool("mock_activity", "{invalid json}", raise_on_tool_fail=False)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "Could not parse JSON" in parsed["error"]

    @pytest.mark.asyncio
    async def test_execute_activity_tool_validation_error(
        self, mock_tool_execution: tuple[MagicMock | AsyncMock, MagicMock | AsyncMock]
    ) -> None:
        class ValidParams(BaseModel):
            name: str
            age: int = Field(gt=0)

        async def mock_activity(params: ValidParams) -> None:
            return None

        mock_activity_fn, mock_hints = mock_tool_execution
        mock_activity_fn.return_value = mock_activity
        mock_hints.return_value = ({"params": ValidParams}, None)

        invalid_args = json.dumps({"name": "test", "age": -5})

        with pytest.raises(WorkflowsException, match="Invalid arguments for tool"):
            await execute_activity_tool("mock_activity", invalid_args, raise_on_tool_fail=True)

        result = await execute_activity_tool("mock_activity", invalid_args, raise_on_tool_fail=False)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "Invalid arguments for tool" in parsed["error"]
        assert "age" in parsed["error"]

    @pytest.mark.asyncio
    async def test_execute_activity_tool_missing_required_field(
        self, mock_tool_execution: tuple[MagicMock | AsyncMock, MagicMock | AsyncMock]
    ) -> None:
        class ValidParams(BaseModel):
            required_field: str
            optional_field: str = "default"

        async def mock_activity(params: ValidParams) -> None:
            return None

        mock_activity_fn, mock_hints = mock_tool_execution
        mock_activity_fn.return_value = mock_activity
        mock_hints.return_value = ({"params": ValidParams}, None)

        incomplete_args = json.dumps({"params": {"optional_field": "test"}})

        result = await execute_activity_tool("mock_activity", incomplete_args, raise_on_tool_fail=False)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "required_field" in parsed["error"]
        assert "Invalid arguments for tool mock_activity" in parsed["error"]

    @pytest.mark.asyncio
    async def test_execute_activity_tool_successful_execution(
        self, mock_tool_execution: tuple[MagicMock | AsyncMock, MagicMock | AsyncMock]
    ) -> None:
        class ValidParams(BaseModel):
            message: str

        class ValidResult(BaseModel):
            result: str

        async def mock_activity(params: ValidParams) -> ValidResult:
            return ValidResult(result=f"Processed: {params.message}")

        mock_activity_fn, mock_hints = mock_tool_execution
        mock_activity_fn.return_value = mock_activity
        mock_hints.return_value = ({"params": ValidParams}, ValidResult)

        valid_args = json.dumps({"params": {"message": "test"}})

        result2 = await execute_activity_tool("mock_activity", valid_args, raise_on_tool_fail=False)
        result1 = await execute_activity_tool("mock_activity", valid_args, raise_on_tool_fail=True)

        assert result1 == result2
        parsed = json.loads(result1)
        assert parsed["result"] == "Processed: test"

    @pytest.mark.asyncio
    async def test_execute_activity_tool_invalid_tool_name(
        self, mock_tool_execution: tuple[MagicMock | AsyncMock, MagicMock | AsyncMock]
    ) -> None:
        mock_activity_fn, mock_hints = mock_tool_execution
        mock_activity_fn.return_value = None

        with pytest.raises(WorkflowsException) as exc_info:
            await execute_activity_tool("nonexistent_tool", "{}", raise_on_tool_fail=True)
        assert exc_info.value.code == ErrorCode.ACTIVITY_NOT_FOUND_ERROR

        result = await execute_activity_tool("nonexistent_tool", "{}", raise_on_tool_fail=False)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "Invalid tool name nonexistent_tool" in parsed["error"]
        assert "Could not find it in the declared agent tools" in parsed["error"]
