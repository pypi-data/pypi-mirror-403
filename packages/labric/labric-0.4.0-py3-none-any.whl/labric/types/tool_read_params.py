# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Literal, Required, TypedDict

__all__ = ["ToolReadParams"]


class ToolReadParams(TypedDict, total=False):
    filters: Required[Dict[str, object]]
    """Django-style filter conditions to apply to the query.

    Keys are field names (with optional lookups like **gt, **contains, etc.) and
    values are the filter values. Pass an empty dict {} to retrieve all records.
    """

    target_name: Required[str]
    """The name of the table to read data from.

    Must be an existing table in your organization.
    """

    target_type: Required[Literal["table"]]
    """The type of target to read from.

    Currently only 'table' is supported for user-defined Labric tables.
    """

    mode: Literal["single", "multiple"]
    """The read mode.

    'single' expects exactly one matching record and returns it (raises 404 if none
    found, 400 if multiple found). 'multiple' returns all matching records as a
    list.
    """
