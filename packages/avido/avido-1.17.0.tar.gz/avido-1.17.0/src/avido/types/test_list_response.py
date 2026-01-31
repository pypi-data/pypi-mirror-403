# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "TestListResponse",
    "Eval",
    "EvalDefinition",
    "EvalDefinitionApplication",
    "EvalDefinitionGlobalConfig",
    "EvalDefinitionGlobalConfigCriterion",
    "EvalDefinitionGlobalConfigGroundTruth",
    "EvalDefinitionGlobalConfigOutputMatchStringConfigOutput",
    "EvalDefinitionGlobalConfigOutputMatchStringConfigOutputExtract",
    "EvalDefinitionGlobalConfigOutputMatchListConfigOutput",
    "EvalDefinitionGlobalConfigOutputMatchListConfigOutputExtract",
    "EvalResults",
    "EvalResultsUnionMember0",
    "EvalResultsUnionMember1",
    "EvalResultsUnionMember2",
    "EvalResultsUnionMember2AnswerRelevancy",
    "EvalResultsUnionMember2AnswerRelevancyMetadata",
    "EvalResultsUnionMember2AnswerRelevancyMetadataQuestion",
    "EvalResultsUnionMember2AnswerRelevancyMetadataSimilarity",
    "EvalResultsUnionMember2ContextPrecision",
    "EvalResultsUnionMember2ContextPrecisionMetadata",
    "EvalResultsUnionMember2ContextRelevancy",
    "EvalResultsUnionMember2ContextRelevancyMetadata",
    "EvalResultsUnionMember2ContextRelevancyMetadataRelevantSentence",
    "EvalResultsUnionMember2Faithfulness",
    "EvalResultsUnionMember2FaithfulnessMetadata",
    "EvalResultsUnionMember2FaithfulnessMetadataFaithfulness",
    "EvalResultsUnionMember3",
    "EvalResultsUnionMember3Metadata",
    "EvalResultsUnionMember4",
    "EvalResultsUnionMember4Classification",
    "EvalResultsUnionMember5",
    "EvalResultsUnionMember5Missing",
    "Task",
    "Result",
]


class EvalDefinitionApplication(BaseModel):
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


class EvalDefinitionGlobalConfigCriterion(BaseModel):
    criterion: str
    """The criterion describes what our evaluation LLM must look for in the response.

    Remember that the answer to the criterion must be as a pass/fail.
    """


class EvalDefinitionGlobalConfigGroundTruth(BaseModel):
    ground_truth: str = FieldInfo(alias="groundTruth")
    """
    The ground truth is the most correct answer to the task that we measure the
    response against
    """


class EvalDefinitionGlobalConfigOutputMatchStringConfigOutputExtract(BaseModel):
    flags: str

    group: Union[int, List[int]]

    pattern: str


class EvalDefinitionGlobalConfigOutputMatchStringConfigOutput(BaseModel):
    type: Literal["string"]

    extract: Optional[EvalDefinitionGlobalConfigOutputMatchStringConfigOutputExtract] = None


class EvalDefinitionGlobalConfigOutputMatchListConfigOutputExtract(BaseModel):
    flags: str

    group: Union[int, List[int]]

    pattern: str


class EvalDefinitionGlobalConfigOutputMatchListConfigOutput(BaseModel):
    match_mode: Literal["exact_unordered", "contains"] = FieldInfo(alias="matchMode")

    type: Literal["list"]

    extract: Optional[EvalDefinitionGlobalConfigOutputMatchListConfigOutputExtract] = None

    pass_threshold: Optional[float] = FieldInfo(alias="passThreshold", default=None)

    score_metric: Optional[Literal["f1", "precision", "recall"]] = FieldInfo(alias="scoreMetric", default=None)


EvalDefinitionGlobalConfig: TypeAlias = Union[
    EvalDefinitionGlobalConfigCriterion,
    EvalDefinitionGlobalConfigGroundTruth,
    EvalDefinitionGlobalConfigOutputMatchStringConfigOutput,
    EvalDefinitionGlobalConfigOutputMatchListConfigOutput,
]


class EvalDefinition(BaseModel):
    id: str

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the eval definition was created"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the eval definition was last modified"""

    name: str

    type: Literal["NATURALNESS", "STYLE", "RECALL", "CUSTOM", "FACT", "OUTPUT_MATCH"]

    application: Optional[EvalDefinitionApplication] = None
    """Application configuration and metadata"""

    global_config: Optional[EvalDefinitionGlobalConfig] = FieldInfo(alias="globalConfig", default=None)

    style_guide_id: Optional[str] = FieldInfo(alias="styleGuideId", default=None)


class EvalResultsUnionMember0(BaseModel):
    analysis: str

    clarity: float

    coherence: float

    engagingness: float

    naturalness: float

    relevance: float


class EvalResultsUnionMember1(BaseModel):
    analysis: str
    """
    A brief explanation for your rating, referring to specific aspects of the
    response and the query. Make sure that the explanation is formatted as markdown,
    and that it is easy to read and understand.
    """

    score: float
    """The score of the response based on the style guide from 1-5"""


class EvalResultsUnionMember2AnswerRelevancyMetadataQuestion(BaseModel):
    question: str


class EvalResultsUnionMember2AnswerRelevancyMetadataSimilarity(BaseModel):
    question: str

    score: float


class EvalResultsUnionMember2AnswerRelevancyMetadata(BaseModel):
    questions: List[EvalResultsUnionMember2AnswerRelevancyMetadataQuestion]

    similarity: List[EvalResultsUnionMember2AnswerRelevancyMetadataSimilarity]


class EvalResultsUnionMember2AnswerRelevancy(BaseModel):
    name: str

    score: float

    error: Optional[str] = None

    metadata: Optional[EvalResultsUnionMember2AnswerRelevancyMetadata] = None


class EvalResultsUnionMember2ContextPrecisionMetadata(BaseModel):
    reason: str

    verdict: int


class EvalResultsUnionMember2ContextPrecision(BaseModel):
    name: str

    score: float

    error: Optional[str] = None

    metadata: Optional[EvalResultsUnionMember2ContextPrecisionMetadata] = None


class EvalResultsUnionMember2ContextRelevancyMetadataRelevantSentence(BaseModel):
    reasons: List[str]

    sentence: str


class EvalResultsUnionMember2ContextRelevancyMetadata(BaseModel):
    relevant_sentences: List[EvalResultsUnionMember2ContextRelevancyMetadataRelevantSentence] = FieldInfo(
        alias="relevantSentences"
    )


class EvalResultsUnionMember2ContextRelevancy(BaseModel):
    name: str

    score: float

    error: Optional[str] = None

    metadata: Optional[EvalResultsUnionMember2ContextRelevancyMetadata] = None


class EvalResultsUnionMember2FaithfulnessMetadataFaithfulness(BaseModel):
    reason: str

    statement: str

    verdict: int

    classification: Optional[Literal["UNSUPPORTED_CLAIM", "CONTRADICTION", "PARTIAL_HALLUCINATION", "SCOPE_DRIFT"]] = (
        None
    )
    """Classification of the hallucination type (only present when verdict is 0)"""


class EvalResultsUnionMember2FaithfulnessMetadata(BaseModel):
    faithfulness: List[EvalResultsUnionMember2FaithfulnessMetadataFaithfulness]

    statements: List[str]


class EvalResultsUnionMember2Faithfulness(BaseModel):
    name: str

    score: float

    error: Optional[str] = None

    metadata: Optional[EvalResultsUnionMember2FaithfulnessMetadata] = None


class EvalResultsUnionMember2(BaseModel):
    answer_relevancy: EvalResultsUnionMember2AnswerRelevancy = FieldInfo(alias="AnswerRelevancy")

    context_precision: EvalResultsUnionMember2ContextPrecision = FieldInfo(alias="ContextPrecision")

    context_relevancy: EvalResultsUnionMember2ContextRelevancy = FieldInfo(alias="ContextRelevancy")

    faithfulness: EvalResultsUnionMember2Faithfulness = FieldInfo(alias="Faithfulness")


class EvalResultsUnionMember3Metadata(BaseModel):
    rationale: str


class EvalResultsUnionMember3(BaseModel):
    name: str

    score: int

    error: Optional[str] = None

    metadata: Optional[EvalResultsUnionMember3Metadata] = None


class EvalResultsUnionMember4Classification(BaseModel):
    fn: List[str] = FieldInfo(alias="FN")
    """False negatives: Statements found in the ground truth but omitted in the answer"""

    fp: List[str] = FieldInfo(alias="FP")
    """
    False positives: Statements present in the answer but not found in the ground
    truth
    """

    tp: List[str] = FieldInfo(alias="TP")
    """
    True positives: Statements that are present in both the answer and the ground
    truth
    """


class EvalResultsUnionMember4(BaseModel):
    classification: EvalResultsUnionMember4Classification

    score: float
    """The F1 score of the response based on the fact checker (0-1)"""

    error: Optional[str] = None

    metadata: Optional[object] = None


class EvalResultsUnionMember5Missing(BaseModel):
    have: float

    need: float

    value: str


class EvalResultsUnionMember5(BaseModel):
    reason: str

    score: float

    expected: Optional[str] = None

    expected_list: Optional[List[str]] = FieldInfo(alias="expectedList", default=None)

    f1: Optional[float] = None

    got: Optional[str] = None

    got_list: Optional[List[str]] = FieldInfo(alias="gotList", default=None)

    match_mode: Optional[Literal["exact_unordered", "contains"]] = FieldInfo(alias="matchMode", default=None)

    missing: Optional[List[EvalResultsUnionMember5Missing]] = None

    precision: Optional[float] = None

    recall: Optional[float] = None

    score_metric: Optional[Literal["f1", "precision", "recall"]] = FieldInfo(alias="scoreMetric", default=None)

    tp: Optional[float] = None


EvalResults: TypeAlias = Union[
    EvalResultsUnionMember0,
    EvalResultsUnionMember1,
    EvalResultsUnionMember2,
    EvalResultsUnionMember3,
    EvalResultsUnionMember4,
    EvalResultsUnionMember5,
]


class Eval(BaseModel):
    """Complete evaluation information"""

    id: str
    """Unique identifier of the evaluation"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the evaluation was created"""

    definition: EvalDefinition

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the evaluation was last modified"""

    org_id: str = FieldInfo(alias="orgId")
    """Organization ID that owns this evaluation"""

    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]
    """Status of the evaluation/test"""

    passed: Optional[bool] = None
    """Whether the evaluation passed"""

    results: Optional[EvalResults] = None
    """Results of the evaluation (structure depends on eval type)."""

    score: Optional[float] = None
    """Overall score of the evaluation"""


class Task(BaseModel):
    id: str
    """The unique identifier of the task"""

    title: str
    """The title of the task"""

    topic_id: Optional[str] = FieldInfo(alias="topicId", default=None)
    """The ID of the topic this task belongs to"""


class Result(BaseModel):
    """Aggregated test result with pass/fail statistics"""

    average_score: float = FieldInfo(alias="averageScore")

    failed: int

    passed: int

    pass_rate: float = FieldInfo(alias="passRate")

    total: int


class TestListResponse(BaseModel):
    __test__ = False
    id: str
    """Unique identifier of the run"""

    application_id: str = FieldInfo(alias="applicationId")
    """The ID of the application this test belongs to"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the test was created"""

    evals: List[Eval]
    """Array of evaluations in this run"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the test was last modified"""

    run_id: str = FieldInfo(alias="runId")
    """The unique identifier of the run"""

    run_type: Literal["MANUAL", "SCHEDULED", "EXPERIMENT", "MONITORING"] = FieldInfo(alias="runType")
    """The type of run this test belongs to"""

    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]
    """Status of the evaluation/test"""

    task: Task

    task_id: str = FieldInfo(alias="taskId")
    """The unique identifier of the task"""

    result: Optional[Result] = None
    """Aggregated test result with pass/fail statistics"""
