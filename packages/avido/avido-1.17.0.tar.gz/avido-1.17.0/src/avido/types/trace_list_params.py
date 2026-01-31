# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["TraceListParams"]


class TraceListParams(TypedDict, total=False):
    end_date: Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]
    """Filter traces created before this date (inclusive)."""

    limit: int
    """Number of items to include in the result set."""

    order_by: Annotated[str, PropertyInfo(alias="orderBy")]
    """Field to order by in the result set."""

    order_dir: Annotated[Literal["asc", "desc"], PropertyInfo(alias="orderDir")]
    """Order direction."""

    reference_id: Annotated[str, PropertyInfo(alias="referenceId")]
    """Filter traces by reference ID"""

    skip: int
    """Number of items to skip before starting to collect the result set."""

    start_date: Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]
    """Filter traces created after this date (inclusive)."""

    test_id: Annotated[str, PropertyInfo(alias="testId")]
    """Filter traces by test ID"""
