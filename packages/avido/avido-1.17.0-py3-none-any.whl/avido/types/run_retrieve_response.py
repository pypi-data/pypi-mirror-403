# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["RunRetrieveResponse", "Run", "RunResult", "RunResultEval"]


class RunResultEval(BaseModel):
    id: str

    average_score: float = FieldInfo(alias="averageScore")

    failed: int

    name: str

    passed: int

    pass_rate: float = FieldInfo(alias="passRate")

    total: int

    type: Literal["NATURALNESS", "STYLE", "RECALL", "CUSTOM", "FACT", "OUTPUT_MATCH"]


class RunResult(BaseModel):
    """Aggregated run result with pass/fail statistics and average score"""

    average_score: float = FieldInfo(alias="averageScore")

    evals: List[RunResultEval]

    failed: int

    passed: int

    pass_rate: float = FieldInfo(alias="passRate")

    total: int


class Run(BaseModel):
    """A Run represents a batch of tests triggered by a single task"""

    id: str
    """Unique identifier of the run"""

    application_id: str = FieldInfo(alias="applicationId")
    """The ID of the application this test belongs to"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the run was created"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the run was last modified"""

    type: Literal["MANUAL", "SCHEDULED", "EXPERIMENT", "MONITORING"]

    experiment_variant_id: Optional[str] = FieldInfo(alias="experimentVariantId", default=None)
    """Optional ID of the experiment variant this run belongs to"""

    result: Optional[RunResult] = None
    """Aggregated run result with pass/fail statistics and average score"""


class RunRetrieveResponse(BaseModel):
    """Successful response containing the run data"""

    run: Run
    """A Run represents a batch of tests triggered by a single task"""
