# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "TestRetrieveResponse",
    "Test",
    "TestEval",
    "TestEvalDefinition",
    "TestEvalDefinitionApplication",
    "TestEvalDefinitionGlobalConfig",
    "TestEvalDefinitionGlobalConfigCriterion",
    "TestEvalDefinitionGlobalConfigGroundTruth",
    "TestEvalDefinitionGlobalConfigOutputMatchStringConfigOutput",
    "TestEvalDefinitionGlobalConfigOutputMatchStringConfigOutputExtract",
    "TestEvalDefinitionGlobalConfigOutputMatchListConfigOutput",
    "TestEvalDefinitionGlobalConfigOutputMatchListConfigOutputExtract",
    "TestEvalResults",
    "TestEvalResultsUnionMember0",
    "TestEvalResultsUnionMember1",
    "TestEvalResultsUnionMember2",
    "TestEvalResultsUnionMember2AnswerRelevancy",
    "TestEvalResultsUnionMember2AnswerRelevancyMetadata",
    "TestEvalResultsUnionMember2AnswerRelevancyMetadataQuestion",
    "TestEvalResultsUnionMember2AnswerRelevancyMetadataSimilarity",
    "TestEvalResultsUnionMember2ContextPrecision",
    "TestEvalResultsUnionMember2ContextPrecisionMetadata",
    "TestEvalResultsUnionMember2ContextRelevancy",
    "TestEvalResultsUnionMember2ContextRelevancyMetadata",
    "TestEvalResultsUnionMember2ContextRelevancyMetadataRelevantSentence",
    "TestEvalResultsUnionMember2Faithfulness",
    "TestEvalResultsUnionMember2FaithfulnessMetadata",
    "TestEvalResultsUnionMember2FaithfulnessMetadataFaithfulness",
    "TestEvalResultsUnionMember3",
    "TestEvalResultsUnionMember3Metadata",
    "TestEvalResultsUnionMember4",
    "TestEvalResultsUnionMember4Classification",
    "TestEvalResultsUnionMember5",
    "TestEvalResultsUnionMember5Missing",
    "TestResult",
]


class TestEvalDefinitionApplication(BaseModel):
    __test__ = False
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


class TestEvalDefinitionGlobalConfigCriterion(BaseModel):
    __test__ = False
    criterion: str
    """The criterion describes what our evaluation LLM must look for in the response.

    Remember that the answer to the criterion must be as a pass/fail.
    """


class TestEvalDefinitionGlobalConfigGroundTruth(BaseModel):
    __test__ = False
    ground_truth: str = FieldInfo(alias="groundTruth")
    """
    The ground truth is the most correct answer to the task that we measure the
    response against
    """


class TestEvalDefinitionGlobalConfigOutputMatchStringConfigOutputExtract(BaseModel):
    __test__ = False
    flags: str

    group: Union[int, List[int]]

    pattern: str


class TestEvalDefinitionGlobalConfigOutputMatchStringConfigOutput(BaseModel):
    __test__ = False
    type: Literal["string"]

    extract: Optional[TestEvalDefinitionGlobalConfigOutputMatchStringConfigOutputExtract] = None


class TestEvalDefinitionGlobalConfigOutputMatchListConfigOutputExtract(BaseModel):
    __test__ = False
    flags: str

    group: Union[int, List[int]]

    pattern: str


class TestEvalDefinitionGlobalConfigOutputMatchListConfigOutput(BaseModel):
    __test__ = False
    match_mode: Literal["exact_unordered", "contains"] = FieldInfo(alias="matchMode")

    type: Literal["list"]

    extract: Optional[TestEvalDefinitionGlobalConfigOutputMatchListConfigOutputExtract] = None

    pass_threshold: Optional[float] = FieldInfo(alias="passThreshold", default=None)

    score_metric: Optional[Literal["f1", "precision", "recall"]] = FieldInfo(alias="scoreMetric", default=None)


TestEvalDefinitionGlobalConfig: TypeAlias = Union[
    TestEvalDefinitionGlobalConfigCriterion,
    TestEvalDefinitionGlobalConfigGroundTruth,
    TestEvalDefinitionGlobalConfigOutputMatchStringConfigOutput,
    TestEvalDefinitionGlobalConfigOutputMatchListConfigOutput,
]


class TestEvalDefinition(BaseModel):
    __test__ = False
    id: str

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the eval definition was created"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the eval definition was last modified"""

    name: str

    type: Literal["NATURALNESS", "STYLE", "RECALL", "CUSTOM", "FACT", "OUTPUT_MATCH"]

    application: Optional[TestEvalDefinitionApplication] = None
    """Application configuration and metadata"""

    global_config: Optional[TestEvalDefinitionGlobalConfig] = FieldInfo(alias="globalConfig", default=None)

    style_guide_id: Optional[str] = FieldInfo(alias="styleGuideId", default=None)


class TestEvalResultsUnionMember0(BaseModel):
    __test__ = False
    analysis: str

    clarity: float

    coherence: float

    engagingness: float

    naturalness: float

    relevance: float


class TestEvalResultsUnionMember1(BaseModel):
    __test__ = False
    analysis: str
    """
    A brief explanation for your rating, referring to specific aspects of the
    response and the query. Make sure that the explanation is formatted as markdown,
    and that it is easy to read and understand.
    """

    score: float
    """The score of the response based on the style guide from 1-5"""


class TestEvalResultsUnionMember2AnswerRelevancyMetadataQuestion(BaseModel):
    __test__ = False
    question: str


class TestEvalResultsUnionMember2AnswerRelevancyMetadataSimilarity(BaseModel):
    __test__ = False
    question: str

    score: float


class TestEvalResultsUnionMember2AnswerRelevancyMetadata(BaseModel):
    __test__ = False
    questions: List[TestEvalResultsUnionMember2AnswerRelevancyMetadataQuestion]

    similarity: List[TestEvalResultsUnionMember2AnswerRelevancyMetadataSimilarity]


class TestEvalResultsUnionMember2AnswerRelevancy(BaseModel):
    __test__ = False
    name: str

    score: float

    error: Optional[str] = None

    metadata: Optional[TestEvalResultsUnionMember2AnswerRelevancyMetadata] = None


class TestEvalResultsUnionMember2ContextPrecisionMetadata(BaseModel):
    __test__ = False
    reason: str

    verdict: int


class TestEvalResultsUnionMember2ContextPrecision(BaseModel):
    __test__ = False
    name: str

    score: float

    error: Optional[str] = None

    metadata: Optional[TestEvalResultsUnionMember2ContextPrecisionMetadata] = None


class TestEvalResultsUnionMember2ContextRelevancyMetadataRelevantSentence(BaseModel):
    __test__ = False
    reasons: List[str]

    sentence: str


class TestEvalResultsUnionMember2ContextRelevancyMetadata(BaseModel):
    __test__ = False
    relevant_sentences: List[TestEvalResultsUnionMember2ContextRelevancyMetadataRelevantSentence] = FieldInfo(
        alias="relevantSentences"
    )


class TestEvalResultsUnionMember2ContextRelevancy(BaseModel):
    __test__ = False
    name: str

    score: float

    error: Optional[str] = None

    metadata: Optional[TestEvalResultsUnionMember2ContextRelevancyMetadata] = None


class TestEvalResultsUnionMember2FaithfulnessMetadataFaithfulness(BaseModel):
    __test__ = False
    reason: str

    statement: str

    verdict: int

    classification: Optional[Literal["UNSUPPORTED_CLAIM", "CONTRADICTION", "PARTIAL_HALLUCINATION", "SCOPE_DRIFT"]] = (
        None
    )
    """Classification of the hallucination type (only present when verdict is 0)"""


class TestEvalResultsUnionMember2FaithfulnessMetadata(BaseModel):
    __test__ = False
    faithfulness: List[TestEvalResultsUnionMember2FaithfulnessMetadataFaithfulness]

    statements: List[str]


class TestEvalResultsUnionMember2Faithfulness(BaseModel):
    __test__ = False
    name: str

    score: float

    error: Optional[str] = None

    metadata: Optional[TestEvalResultsUnionMember2FaithfulnessMetadata] = None


class TestEvalResultsUnionMember2(BaseModel):
    __test__ = False
    answer_relevancy: TestEvalResultsUnionMember2AnswerRelevancy = FieldInfo(alias="AnswerRelevancy")

    context_precision: TestEvalResultsUnionMember2ContextPrecision = FieldInfo(alias="ContextPrecision")

    context_relevancy: TestEvalResultsUnionMember2ContextRelevancy = FieldInfo(alias="ContextRelevancy")

    faithfulness: TestEvalResultsUnionMember2Faithfulness = FieldInfo(alias="Faithfulness")


class TestEvalResultsUnionMember3Metadata(BaseModel):
    __test__ = False
    rationale: str


class TestEvalResultsUnionMember3(BaseModel):
    __test__ = False
    name: str

    score: int

    error: Optional[str] = None

    metadata: Optional[TestEvalResultsUnionMember3Metadata] = None


class TestEvalResultsUnionMember4Classification(BaseModel):
    __test__ = False
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


class TestEvalResultsUnionMember4(BaseModel):
    __test__ = False
    classification: TestEvalResultsUnionMember4Classification

    score: float
    """The F1 score of the response based on the fact checker (0-1)"""

    error: Optional[str] = None

    metadata: Optional[object] = None


class TestEvalResultsUnionMember5Missing(BaseModel):
    __test__ = False
    have: float

    need: float

    value: str


class TestEvalResultsUnionMember5(BaseModel):
    __test__ = False
    reason: str

    score: float

    expected: Optional[str] = None

    expected_list: Optional[List[str]] = FieldInfo(alias="expectedList", default=None)

    f1: Optional[float] = None

    got: Optional[str] = None

    got_list: Optional[List[str]] = FieldInfo(alias="gotList", default=None)

    match_mode: Optional[Literal["exact_unordered", "contains"]] = FieldInfo(alias="matchMode", default=None)

    missing: Optional[List[TestEvalResultsUnionMember5Missing]] = None

    precision: Optional[float] = None

    recall: Optional[float] = None

    score_metric: Optional[Literal["f1", "precision", "recall"]] = FieldInfo(alias="scoreMetric", default=None)

    tp: Optional[float] = None


TestEvalResults: TypeAlias = Union[
    TestEvalResultsUnionMember0,
    TestEvalResultsUnionMember1,
    TestEvalResultsUnionMember2,
    TestEvalResultsUnionMember3,
    TestEvalResultsUnionMember4,
    TestEvalResultsUnionMember5,
]


class TestEval(BaseModel):
    __test__ = False
    """Complete evaluation information"""
    id: str
    """Unique identifier of the evaluation"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the evaluation was created"""

    definition: TestEvalDefinition

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the evaluation was last modified"""

    org_id: str = FieldInfo(alias="orgId")
    """Organization ID that owns this evaluation"""

    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]
    """Status of the evaluation/test"""

    passed: Optional[bool] = None
    """Whether the evaluation passed"""

    results: Optional[TestEvalResults] = None
    """Results of the evaluation (structure depends on eval type)."""

    score: Optional[float] = None
    """Overall score of the evaluation"""


class TestResult(BaseModel):
    __test__ = False
    """Aggregated test result with pass/fail statistics"""
    average_score: float = FieldInfo(alias="averageScore")

    failed: int

    passed: int

    pass_rate: float = FieldInfo(alias="passRate")

    total: int


class Test(BaseModel):
    __test__ = False
    """A Test represents a single test applying all the linked evals on a Trace"""
    id: str
    """Unique identifier of the run"""

    application_id: str = FieldInfo(alias="applicationId")
    """The ID of the application this test belongs to"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the test was created"""

    evals: List[TestEval]
    """Array of evaluations in this run"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the test was last modified"""

    run_id: str = FieldInfo(alias="runId")
    """The unique identifier of the run"""

    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]
    """Status of the evaluation/test"""

    task_id: str = FieldInfo(alias="taskId")
    """The unique identifier of the task"""

    result: Optional[TestResult] = None
    """Aggregated test result with pass/fail statistics"""


class TestRetrieveResponse(BaseModel):
    __test__ = False
    test: Test
    """A Test represents a single test applying all the linked evals on a Trace"""
