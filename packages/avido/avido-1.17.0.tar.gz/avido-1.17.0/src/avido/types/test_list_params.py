# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["TestListParams"]


class TestListParams(TypedDict, total=False):
    eval_definition_id: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="evalDefinitionId")]]
    """Filter tests by eval definition ID"""

    experiment_variant_id: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="experimentVariantId")]]
    """Filter tests by experiment variant ID"""

    pass_rate_statuses: Required[
        Annotated[List[Literal["success", "warning", "error"]], PropertyInfo(alias="passRateStatuses")]
    ]
    """Filter by pass rate status badges (success: >75%, warning: 51-75%, error: ≤50%)"""

    run_type: Required[
        Annotated[List[Literal["MANUAL", "SCHEDULED", "EXPERIMENT", "MONITORING"]], PropertyInfo(alias="runType")]
    ]
    """Filter tests by run type (MANUAL, SCHEDULED, EXPERIMENT)"""

    status: Required[List[Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]]]
    """Filter by test status (e.g. COMPLETED, FAILED)"""

    task_id: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="taskId")]]
    """Filter tests by task ID"""

    end_date: Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]
    """Filter eval runs before this date (inclusive)."""

    limit: int
    """Number of items to include in the result set."""

    order_by: Annotated[str, PropertyInfo(alias="orderBy")]
    """Field to order by in the result set."""

    order_dir: Annotated[Literal["asc", "desc"], PropertyInfo(alias="orderDir")]
    """Order direction."""

    skip: int
    """Number of items to skip before starting to collect the result set."""

    start_date: Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]
    """Filter eval runs after this date (inclusive)."""
