"""Tool validation validator implementation."""

from __future__ import annotations

from typing import Any, List, Mapping, Optional

from accuralai_core.config.schema import ValidatorSettings
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse
from accuralai_core.contracts.protocols import Validator

from ..base import ValidationEvent, append_event


class ToolValidatorOptions:
    """Configuration options for the tool validator."""
    
    def __init__(
        self,
        *,
        available_tools: Optional[List[str]] = None,
        failure_reason: str = "error",
        provide_feedback: bool = True,
        feedback_message: Optional[str] = None,
    ):
        self.available_tools = set(available_tools or [])
        self.failure_reason = failure_reason
        self.provide_feedback = provide_feedback
        self.feedback_message = feedback_message or (
            "I attempted to use a tool that is not available. "
            "I am a general purpose AI assistant and can help with a wide variety of topics and tasks. "
            "Please provide the answer directly without using tools, or use one of the available tools."
        )


class ToolValidator(Validator):
    """Validates that tool calls reference available tools and provides feedback for invalid calls."""

    def __init__(self, *, options: ToolValidatorOptions, validator_id: str) -> None:
        self._options = options
        self._validator_id = validator_id

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        """Validate tool calls in the response."""
        # Check if there are tool calls in the response metadata
        tool_calls = response.metadata.get("tool_calls", [])
        
        if not tool_calls:
            return response
        
        # Check each tool call
        invalid_tools = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name") or tool_call.get("functionName", "")
            if tool_name and tool_name not in self._options.available_tools:
                invalid_tools.append(tool_name)
        
        if invalid_tools:
            # Update the response to provide feedback
            updated_response = response.model_copy(
                update={
                    "output_text": self._options.feedback_message,
                    "finish_reason": self._options.failure_reason,
                }
            )
            
            # Add validation event
            event = ValidationEvent(
                validator_id=self._validator_id,
                category="tool_validation",
                details={
                    "invalid_tools": invalid_tools,
                    "available_tools": list(self._options.available_tools),
                    "feedback_provided": self._options.provide_feedback,
                },
            )
            
            return append_event(updated_response, event)
        
        return response


async def build_tool_validator(
    *,
    config: ValidatorSettings | Mapping[str, Any] | None = None,
    validator_id: Optional[str] = None,
    **_: Any,
) -> Validator:
    """Factory registered for the tool validator."""
    options_payload: Mapping[str, Any] | ToolValidatorOptions | None = None
    if isinstance(config, ValidatorSettings):
        options_payload = config.options or {}
        validator_id = validator_id or config.id or "validator.tool"
    else:
        options_payload = config
        validator_id = validator_id or "validator.tool"

    # Extract available tools from the request context if available
    available_tools = []
    if isinstance(options_payload, dict):
        available_tools = options_payload.get("available_tools", [])
    
    options = ToolValidatorOptions(
        available_tools=available_tools,
        failure_reason=options_payload.get("failure_reason", "error") if isinstance(options_payload, dict) else "error",
        provide_feedback=options_payload.get("provide_feedback", True) if isinstance(options_payload, dict) else True,
        feedback_message=options_payload.get("feedback_message") if isinstance(options_payload, dict) else None,
    )
    
    return ToolValidator(options=options, validator_id=validator_id)
