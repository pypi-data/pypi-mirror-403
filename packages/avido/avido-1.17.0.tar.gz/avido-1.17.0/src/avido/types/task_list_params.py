# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["TaskListParams"]


class TaskListParams(TypedDict, total=False):
    eval_definition_id: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="evalDefinitionId")]]
    """Filter tasks by eval definition ID"""

    status: Required[List[Literal["success", "warning", "error", "no-tests"]]]
    """Filter tasks by status"""

    topic_id: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="topicId")]]
    """Filter tasks by topic ID"""

    limit: int
    """Number of items to include in the result set."""

    order_by: Annotated[str, PropertyInfo(alias="orderBy")]
    """Field to order by in the result set."""

    order_dir: Annotated[Literal["asc", "desc"], PropertyInfo(alias="orderDir")]
    """Order direction."""

    skip: int
    """Number of items to skip before starting to collect the result set."""

    tag_id: Annotated[SequenceNotStr[str], PropertyInfo(alias="tagId")]
    """Filter tasks by tag ID"""
