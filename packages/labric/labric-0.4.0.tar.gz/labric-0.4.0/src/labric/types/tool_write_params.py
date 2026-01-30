# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Literal, Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["ToolWriteParams"]


class ToolWriteParams(TypedDict, total=False):
    data: Required[Iterable[Dict[str, object]]]
    """A list of records to write.

    Each record is a dictionary where keys are column names and values are the data
    to insert or update.
    """

    mode: Required[Literal["create", "create-or-update"]]
    """The write operation mode.

    'create' inserts new records (fails if duplicates exist). 'create-or-update'
    finds existing records by params_to_match_for_update and updates them, or
    creates new records if no match is found.
    """

    target_name: Required[str]
    """The name of the table to write data to.

    Must be an existing table in your organization.
    """

    target_type: Required[Literal["table", "core-table"]]
    """The type of target to write to.

    Use 'table' for user-defined Labric tables, or 'core-table' for built-in system
    tables.
    """

    batch_insert_ok: bool
    """When true, enables bulk insertion for better performance.

    Only available in 'create' mode. Cannot be used with 'create-or-update' mode.
    """

    collect_output: bool
    """When true, the response will include the full data of all written records.

    When false (default), returns an empty list for better performance.
    """

    defaults: Optional[Dict[str, str]]
    """Default values to apply to all records.

    Supports special function names: 'DATETIME_NOW' (current timestamp) and 'UUID4'
    (generate a new UUID). These defaults are applied before the record data, so
    explicit values in data will override defaults.
    """

    dry_run: bool
    """
    When true, validates the write operation without persisting any changes to the
    database. Useful for testing data before committing.
    """

    job_execution_id: Optional[str]
    """Optional ID of an existing job execution to associate this write operation with.

    If not provided, a new job execution will be created automatically.
    """

    job_name: Optional[str]
    """Name for the automatically created job when job_execution_id is not provided.

    Defaults to 'Off-Platform Manual Job' if not specified.
    """

    params_to_match_for_update: Optional[SequenceNotStr[str]]
    """List of field names used to identify existing records for updates.

    Required when mode is 'create-or-update'. The system will search for records
    matching these fields and update them if found, or create new records if not.
    """
