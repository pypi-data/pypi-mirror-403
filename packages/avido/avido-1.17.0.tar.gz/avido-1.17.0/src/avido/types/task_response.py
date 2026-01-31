# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "TaskResponse",
    "Task",
    "TaskEvalDefinition",
    "TaskEvalDefinitionEvalDefinition",
    "TaskEvalDefinitionEvalDefinitionApplication",
    "TaskEvalDefinitionEvalDefinitionGlobalConfig",
    "TaskEvalDefinitionEvalDefinitionGlobalConfigCriterion",
    "TaskEvalDefinitionEvalDefinitionGlobalConfigGroundTruth",
    "TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchStringConfigOutput",
    "TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchStringConfigOutputExtract",
    "TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchListConfigOutput",
    "TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchListConfigOutputExtract",
    "TaskEvalDefinitionConfig",
    "TaskTaskSchedule",
]


class TaskEvalDefinitionEvalDefinitionApplication(BaseModel):
    """Application configuration and metadata"""

    id: str
    """Unique identifier of the application"""

    context: str
    """Context/instructions for the application"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the application was created"""

    description: str
    """Description of the application"""

    environment: Literal["DEV", "PROD"]
    """Environment of the application. Defaults to DEV."""

    language: str
    """Language of the application"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the application was last modified"""

    org_id: str = FieldInfo(alias="orgId")
    """Organization ID that owns this application"""

    slug: str
    """URL-friendly slug for the application"""

    title: str
    """Title of the application"""

    type: Literal["CHATBOT", "AGENT"]
    """Type of the application. Valid values are CHATBOT or AGENT."""


class TaskEvalDefinitionEvalDefinitionGlobalConfigCriterion(BaseModel):
    criterion: str
    """The criterion describes what our evaluation LLM must look for in the response.

    Remember that the answer to the criterion must be as a pass/fail.
    """


class TaskEvalDefinitionEvalDefinitionGlobalConfigGroundTruth(BaseModel):
    ground_truth: str = FieldInfo(alias="groundTruth")
    """
    The ground truth is the most correct answer to the task that we measure the
    response against
    """


class TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchStringConfigOutputExtract(BaseModel):
    flags: str

    group: Union[int, List[int]]

    pattern: str


class TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchStringConfigOutput(BaseModel):
    type: Literal["string"]

    extract: Optional[TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchStringConfigOutputExtract] = None


class TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchListConfigOutputExtract(BaseModel):
    flags: str

    group: Union[int, List[int]]

    pattern: str


class TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchListConfigOutput(BaseModel):
    match_mode: Literal["exact_unordered", "contains"] = FieldInfo(alias="matchMode")

    type: Literal["list"]

    extract: Optional[TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchListConfigOutputExtract] = None

    pass_threshold: Optional[float] = FieldInfo(alias="passThreshold", default=None)

    score_metric: Optional[Literal["f1", "precision", "recall"]] = FieldInfo(alias="scoreMetric", default=None)


TaskEvalDefinitionEvalDefinitionGlobalConfig: TypeAlias = Union[
    TaskEvalDefinitionEvalDefinitionGlobalConfigCriterion,
    TaskEvalDefinitionEvalDefinitionGlobalConfigGroundTruth,
    TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchStringConfigOutput,
    TaskEvalDefinitionEvalDefinitionGlobalConfigOutputMatchListConfigOutput,
]


class TaskEvalDefinitionEvalDefinition(BaseModel):
    id: str

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the eval definition was created"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the eval definition was last modified"""

    name: str

    type: Literal["NATURALNESS", "STYLE", "RECALL", "CUSTOM", "FACT", "OUTPUT_MATCH"]

    application: Optional[TaskEvalDefinitionEvalDefinitionApplication] = None
    """Application configuration and metadata"""

    global_config: Optional[TaskEvalDefinitionEvalDefinitionGlobalConfig] = FieldInfo(
        alias="globalConfig", default=None
    )

    style_guide_id: Optional[str] = FieldInfo(alias="styleGuideId", default=None)


class TaskEvalDefinitionConfig(BaseModel):
    expected: Union[str, List[str]]


class TaskEvalDefinition(BaseModel):
    eval_definition: TaskEvalDefinitionEvalDefinition = FieldInfo(alias="evalDefinition")

    config: Optional[TaskEvalDefinitionConfig] = None


class TaskTaskSchedule(BaseModel):
    """Task schedule schema"""

    criticality: Literal["LOW", "MEDIUM", "HIGH"]

    cron: str

    task_id: str = FieldInfo(alias="taskId")

    last_run_at: Optional[datetime] = FieldInfo(alias="lastRunAt", default=None)

    next_run_at: Optional[datetime] = FieldInfo(alias="nextRunAt", default=None)


class Task(BaseModel):
    """
    A task that represents a specific job-to-be-done by the LLM in the user application.
    """

    id: str
    """The unique identifier of the task"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the task was created"""

    description: str
    """The task description"""

    eval_definitions: List[TaskEvalDefinition] = FieldInfo(alias="evalDefinitions")

    input_examples: List[str] = FieldInfo(alias="inputExamples")
    """Example inputs for the task"""

    metadata: Dict[str, object]
    """Optional metadata associated with the task.

    Returns null when no metadata is stored.
    """

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the task was last modified"""

    pass_rate: float = FieldInfo(alias="passRate")
    """The 30 day pass rate for the task measured in percentage"""

    status: Literal["DEDUCED", "DRAFT", "ACTIVE"]
    """The status of the task.

    DEDUCED tasks are created from unmatched traces, DRAFT tasks are user-facing
    drafts, and ACTIVE tasks are production tasks.
    """

    title: str
    """The title of the task"""

    type: Literal["STATIC", "NORMAL"]
    """The type of task.

    Normal tasks have a dynamic user prompt, while adversarial tasks have a fixed
    user prompt.
    """

    last_test: Optional[datetime] = FieldInfo(alias="lastTest", default=None)
    """The date and time this task was last tested"""

    parent_id: Optional[str] = FieldInfo(alias="parentId", default=None)
    """The ID of the parent task (for DEDUCED tasks linked to a DRAFT)"""

    simulated_prompt_schema: Optional[Dict[str, object]] = FieldInfo(alias="simulatedPromptSchema", default=None)
    """
    JSON schema that defines the structure for user prompts that should be generated
    for tests
    """

    task_schedule: Optional[TaskTaskSchedule] = FieldInfo(alias="taskSchedule", default=None)
    """Task schedule schema"""

    topic_id: Optional[str] = FieldInfo(alias="topicId", default=None)
    """The ID of the topic this task belongs to"""

    trace_id: Optional[str] = FieldInfo(alias="traceId", default=None)
    """The ID of the trace this task was deduced from (only for DEDUCED tasks)"""


class TaskResponse(BaseModel):
    """Successful response containing the task data"""

    task: Task
    """
    A task that represents a specific job-to-be-done by the LLM in the user
    application.
    """
