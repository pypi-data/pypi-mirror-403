# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "TraceListResponse",
    "Step",
    "StepLlmStartStepOutput",
    "StepLlmEndStepOutput",
    "StepLlmEndStepOutputUsage",
    "StepToolStepOutput",
    "StepRetrieverStepOutput",
    "StepLogStepOutput",
    "StepGroupStepOutput",
    "StepResponseStepOutput",
    "StepRequestStepOutput",
]


class StepLlmStartStepOutput(BaseModel):
    """Start of an LLM trace."""

    id: str
    """UUID for the step."""

    event: Literal["start"]

    input: str
    """JSON input for this LLM trace event (e.g., the prompt)."""

    api_model_id: str = FieldInfo(alias="modelId")
    """Model ID or name used for the LLM call."""

    timestamp: datetime
    """When the step was created"""

    trace_id: str = FieldInfo(alias="traceId")
    """UUID referencing the parent trace's ID."""

    type: Literal["llm"]

    group: Optional[str] = None
    """Optionally, the key for a group step to group the step with."""

    metadata: Union[Dict[str, object], List[object], None] = None
    """Extra metadata about this trace event.

    String values are parsed as JSON if possible, otherwise wrapped in { raw: val }.
    """

    name: Optional[str] = None
    """The name of the step."""

    params: Union[Dict[str, object], List[object], None] = None
    """Arbitrary params for the step."""


class StepLlmEndStepOutputUsage(BaseModel):
    """Number of input and output tokens used by the LLM."""

    completion_tokens: int = FieldInfo(alias="completionTokens")
    """Number of completion tokens used by the LLM."""

    prompt_tokens: int = FieldInfo(alias="promptTokens")
    """Number of prompt tokens used by the LLM."""


class StepLlmEndStepOutput(BaseModel):
    """End of an LLM trace."""

    id: str
    """UUID for the step."""

    event: Literal["end"]

    api_model_id: str = FieldInfo(alias="modelId")
    """Model ID or name used for the LLM call."""

    timestamp: datetime
    """When the step was created"""

    trace_id: str = FieldInfo(alias="traceId")
    """UUID referencing the parent trace's ID."""

    type: Literal["llm"]

    group: Optional[str] = None
    """Optionally, the key for a group step to group the step with."""

    metadata: Union[Dict[str, object], List[object], None] = None
    """Extra metadata about this trace event.

    String values are parsed as JSON if possible, otherwise wrapped in { raw: val }.
    """

    name: Optional[str] = None
    """The name of the step."""

    output: Optional[str] = None
    """JSON describing the output.

    String inputs are parsed or wrapped in { message: val }.
    """

    params: Union[Dict[str, object], List[object], None] = None
    """Arbitrary params for the step."""

    usage: Optional[StepLlmEndStepOutputUsage] = None
    """Number of input and output tokens used by the LLM."""


class StepToolStepOutput(BaseModel):
    """Track all tool calls using the Tool Step event"""

    id: str
    """UUID for the step."""

    timestamp: datetime
    """When the step was created"""

    trace_id: str = FieldInfo(alias="traceId")
    """UUID referencing the parent trace's ID."""

    type: Literal["tool"]

    group: Optional[str] = None
    """Optionally, the key for a group step to group the step with."""

    metadata: Union[Dict[str, object], List[object], None] = None
    """Extra metadata about this trace event.

    String values are parsed as JSON if possible, otherwise wrapped in { raw: val }.
    """

    name: Optional[str] = None
    """The name of the step."""

    params: Union[Dict[str, object], List[object], None] = None
    """Arbitrary params for the step."""

    tool_input: Optional[str] = FieldInfo(alias="toolInput", default=None)
    """JSON input for the tool call."""

    tool_output: Optional[str] = FieldInfo(alias="toolOutput", default=None)
    """JSON output from the tool call."""


class StepRetrieverStepOutput(BaseModel):
    """Track all retriever (RAG) calls using the Retriever Step event."""

    id: str
    """UUID for the step."""

    query: str
    """Query used for RAG."""

    result: str
    """Retrieved text"""

    timestamp: datetime
    """When the step was created"""

    trace_id: str = FieldInfo(alias="traceId")
    """UUID referencing the parent trace's ID."""

    type: Literal["retriever"]

    group: Optional[str] = None
    """Optionally, the key for a group step to group the step with."""

    metadata: Union[Dict[str, object], List[object], None] = None
    """Extra metadata about this trace event.

    String values are parsed as JSON if possible, otherwise wrapped in { raw: val }.
    """

    name: Optional[str] = None
    """The name of the step."""

    params: Union[Dict[str, object], List[object], None] = None
    """Arbitrary params for the step."""


class StepLogStepOutput(BaseModel):
    """Track all logs using the Log Step event."""

    id: str
    """UUID for the step."""

    content: str
    """The actual log message for this trace."""

    timestamp: datetime
    """When the step was created"""

    trace_id: str = FieldInfo(alias="traceId")
    """UUID referencing the parent trace's ID."""

    type: Literal["log"]

    group: Optional[str] = None
    """Optionally, the key for a group step to group the step with."""

    metadata: Union[Dict[str, object], List[object], None] = None
    """Extra metadata about this trace event.

    String values are parsed as JSON if possible, otherwise wrapped in { raw: val }.
    """

    name: Optional[str] = None
    """The name of the step."""

    params: Union[Dict[str, object], List[object], None] = None
    """Arbitrary params for the step."""


class StepGroupStepOutput(BaseModel):
    """
    Use this to group multiple steps together, for example a log, llm start, and llm end.
    """

    id: str
    """UUID for the step."""

    key: str
    """
    A unique identifier for the grouping, which must be appended to the
    corresponding steps
    """

    timestamp: datetime
    """When the step was created"""

    trace_id: str = FieldInfo(alias="traceId")
    """UUID referencing the parent trace's ID."""

    type: Literal["group"]

    group: Optional[str] = None
    """Optionally, the key for a group step to group the step with."""

    metadata: Union[Dict[str, object], List[object], None] = None
    """Extra metadata about this trace event.

    String values are parsed as JSON if possible, otherwise wrapped in { raw: val }.
    """

    name: Optional[str] = None
    """The name of the step."""

    params: Union[Dict[str, object], List[object], None] = None
    """Arbitrary params for the step."""


class StepResponseStepOutput(BaseModel):
    """Track AI responses to users using the Response Step event."""

    id: str
    """UUID for the step."""

    content: str
    """The response content from the AI to the user."""

    timestamp: datetime
    """When the step was created"""

    trace_id: str = FieldInfo(alias="traceId")
    """UUID referencing the parent trace's ID."""

    type: Literal["response"]

    group: Optional[str] = None
    """Optionally, the key for a group step to group the step with."""

    metadata: Union[Dict[str, object], List[object], None] = None
    """Extra metadata about this trace event.

    String values are parsed as JSON if possible, otherwise wrapped in { raw: val }.
    """

    name: Optional[str] = None
    """The name of the step."""

    params: Union[Dict[str, object], List[object], None] = None
    """Arbitrary params for the step."""


class StepRequestStepOutput(BaseModel):
    """Track user requests to the AI using the Request Step event."""

    id: str
    """UUID for the step."""

    content: str
    """The request content from the user to the AI."""

    timestamp: datetime
    """When the step was created"""

    trace_id: str = FieldInfo(alias="traceId")
    """UUID referencing the parent trace's ID."""

    type: Literal["request"]

    group: Optional[str] = None
    """Optionally, the key for a group step to group the step with."""

    metadata: Union[Dict[str, object], List[object], None] = None
    """Extra metadata about this trace event.

    String values are parsed as JSON if possible, otherwise wrapped in { raw: val }.
    """

    name: Optional[str] = None
    """The name of the step."""

    params: Union[Dict[str, object], List[object], None] = None
    """Arbitrary params for the step."""


Step: TypeAlias = Union[
    StepLlmStartStepOutput,
    StepLlmEndStepOutput,
    StepToolStepOutput,
    StepRetrieverStepOutput,
    StepLogStepOutput,
    StepGroupStepOutput,
    StepResponseStepOutput,
    StepRequestStepOutput,
]


class TraceListResponse(BaseModel):
    """A trace grouping related steps (e.g. a user-agent interaction or conversation)."""

    id: str
    """Unique Trace ID (UUID)."""

    timestamp: datetime
    """When the trace was created"""

    metadata: Union[Dict[str, object], List[object], None] = None
    """Arbitrary metadata (e.g., userId, source).

    String inputs are parsed as JSON or wrapped in { raw: val }.
    """

    reference_id: Optional[str] = FieldInfo(alias="referenceId", default=None)
    """
    An optional reference ID to link the trace to an existing conversation or
    interaction in your own database.
    """

    steps: Optional[List[Step]] = None
    """The steps associated with the trace."""

    test_id: Optional[str] = FieldInfo(alias="testId", default=None)
    """The associated Test if this was triggered by an Avido eval"""
