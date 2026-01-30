# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable, Optional
from typing_extensions import Literal

import httpx

from ..types import tool_read_params, tool_write_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.tool_read_response import ToolReadResponse
from ..types.tool_write_response import ToolWriteResponse

__all__ = ["ToolsResource", "AsyncToolsResource"]


class ToolsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ToolsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Labric-Platforms/labric-py#accessing-raw-response-data-eg-headers
        """
        return ToolsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ToolsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Labric-Platforms/labric-py#with_streaming_response
        """
        return ToolsResourceWithStreamingResponse(self)

    def read(
        self,
        *,
        filters: Dict[str, object],
        target_name: str,
        target_type: Literal["table"],
        mode: Literal["single", "multiple"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ToolReadResponse:
        """
        Read data from a Labric table with flexible filtering.

        This endpoint allows you to query records from any user-defined table within
        your organization. Results are automatically scoped to your organization's data.

        ## Filtering

        Use Django-style field lookups in the `filters` parameter:

        - Exact match: `{"name": "Sample A"}`
        - Greater than: `{"concentration__gt": 1.0}`
        - Contains: `{"description__contains": "test"}`
        - Multiple conditions: `{"status": "active", "priority__gte": 5}`

        Pass an empty object `{}` to retrieve all records.

        ## Modes

        - **single**: Expects exactly one matching record. Returns 404 if no records
          found, or 400 if multiple records match. Useful when querying by unique
          identifier.
        - **multiple**: Returns all matching records as a list. Use this for general
          queries.

        ## Response

        Returns a list of dictionaries, where each dictionary represents a record with
        all its fields as key-value pairs.

        Args:
          filters: Django-style filter conditions to apply to the query. Keys are field names (with
              optional lookups like **gt, **contains, etc.) and values are the filter values.
              Pass an empty dict {} to retrieve all records.

          target_name: The name of the table to read data from. Must be an existing table in your
              organization.

          target_type: The type of target to read from. Currently only 'table' is supported for
              user-defined Labric tables.

          mode: The read mode. 'single' expects exactly one matching record and returns it
              (raises 404 if none found, 400 if multiple found). 'multiple' returns all
              matching records as a list.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/v1/tools/read",
            body=maybe_transform(
                {
                    "filters": filters,
                    "target_name": target_name,
                    "target_type": target_type,
                    "mode": mode,
                },
                tool_read_params.ToolReadParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ToolReadResponse,
        )

    def write(
        self,
        *,
        data: Iterable[Dict[str, object]],
        mode: Literal["create", "create-or-update"],
        target_name: str,
        target_type: Literal["table", "core-table"],
        batch_insert_ok: bool | Omit = omit,
        collect_output: bool | Omit = omit,
        defaults: Optional[Dict[str, str]] | Omit = omit,
        dry_run: bool | Omit = omit,
        job_execution_id: Optional[str] | Omit = omit,
        job_name: Optional[str] | Omit = omit,
        params_to_match_for_update: Optional[SequenceNotStr[str]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ToolWriteResponse:
        """
        Write data to a Labric table with support for inserts and upserts.

        This endpoint allows you to create new records or update existing records in any
        user-defined table within your organization. All write operations are tracked
        with provenance information for data lineage.

        ## Modes

        - **create**: Insert new records. Use `batch_insert_ok=true` for bulk inserts
          with better performance.
        - **create-or-update**: Upsert operation. Finds existing records by
          `params_to_match_for_update` fields and updates them, or creates new records
          if no match is found.

        ## Default Values

        Use the `defaults` parameter to automatically populate fields:

        - `DATETIME_NOW`: Current timestamp
        - `UUID4`: Generate a new UUID

        ## Job Tracking

        Every write operation is associated with a job execution for provenance
        tracking. Provide `job_execution_id` to link to an existing job, or let the
        system create one automatically (optionally named via `job_name`).

        ## Response

        Returns an empty list by default for performance. Set `collect_output=true` to
        receive the full data of all written records in the response.

        Args:
          data: A list of records to write. Each record is a dictionary where keys are column
              names and values are the data to insert or update.

          mode: The write operation mode. 'create' inserts new records (fails if duplicates
              exist). 'create-or-update' finds existing records by params_to_match_for_update
              and updates them, or creates new records if no match is found.

          target_name: The name of the table to write data to. Must be an existing table in your
              organization.

          target_type: The type of target to write to. Use 'table' for user-defined Labric tables, or
              'core-table' for built-in system tables.

          batch_insert_ok: When true, enables bulk insertion for better performance. Only available in
              'create' mode. Cannot be used with 'create-or-update' mode.

          collect_output: When true, the response will include the full data of all written records. When
              false (default), returns an empty list for better performance.

          defaults:
              Default values to apply to all records. Supports special function names:
              'DATETIME_NOW' (current timestamp) and 'UUID4' (generate a new UUID). These
              defaults are applied before the record data, so explicit values in data will
              override defaults.

          dry_run: When true, validates the write operation without persisting any changes to the
              database. Useful for testing data before committing.

          job_execution_id: Optional ID of an existing job execution to associate this write operation with.
              If not provided, a new job execution will be created automatically.

          job_name: Name for the automatically created job when job_execution_id is not provided.
              Defaults to 'Off-Platform Manual Job' if not specified.

          params_to_match_for_update: List of field names used to identify existing records for updates. Required when
              mode is 'create-or-update'. The system will search for records matching these
              fields and update them if found, or create new records if not.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/v1/tools/write",
            body=maybe_transform(
                {
                    "data": data,
                    "mode": mode,
                    "target_name": target_name,
                    "target_type": target_type,
                    "batch_insert_ok": batch_insert_ok,
                    "collect_output": collect_output,
                    "defaults": defaults,
                    "dry_run": dry_run,
                    "job_execution_id": job_execution_id,
                    "job_name": job_name,
                    "params_to_match_for_update": params_to_match_for_update,
                },
                tool_write_params.ToolWriteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ToolWriteResponse,
        )


class AsyncToolsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncToolsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/Labric-Platforms/labric-py#accessing-raw-response-data-eg-headers
        """
        return AsyncToolsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncToolsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/Labric-Platforms/labric-py#with_streaming_response
        """
        return AsyncToolsResourceWithStreamingResponse(self)

    async def read(
        self,
        *,
        filters: Dict[str, object],
        target_name: str,
        target_type: Literal["table"],
        mode: Literal["single", "multiple"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ToolReadResponse:
        """
        Read data from a Labric table with flexible filtering.

        This endpoint allows you to query records from any user-defined table within
        your organization. Results are automatically scoped to your organization's data.

        ## Filtering

        Use Django-style field lookups in the `filters` parameter:

        - Exact match: `{"name": "Sample A"}`
        - Greater than: `{"concentration__gt": 1.0}`
        - Contains: `{"description__contains": "test"}`
        - Multiple conditions: `{"status": "active", "priority__gte": 5}`

        Pass an empty object `{}` to retrieve all records.

        ## Modes

        - **single**: Expects exactly one matching record. Returns 404 if no records
          found, or 400 if multiple records match. Useful when querying by unique
          identifier.
        - **multiple**: Returns all matching records as a list. Use this for general
          queries.

        ## Response

        Returns a list of dictionaries, where each dictionary represents a record with
        all its fields as key-value pairs.

        Args:
          filters: Django-style filter conditions to apply to the query. Keys are field names (with
              optional lookups like **gt, **contains, etc.) and values are the filter values.
              Pass an empty dict {} to retrieve all records.

          target_name: The name of the table to read data from. Must be an existing table in your
              organization.

          target_type: The type of target to read from. Currently only 'table' is supported for
              user-defined Labric tables.

          mode: The read mode. 'single' expects exactly one matching record and returns it
              (raises 404 if none found, 400 if multiple found). 'multiple' returns all
              matching records as a list.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/v1/tools/read",
            body=await async_maybe_transform(
                {
                    "filters": filters,
                    "target_name": target_name,
                    "target_type": target_type,
                    "mode": mode,
                },
                tool_read_params.ToolReadParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ToolReadResponse,
        )

    async def write(
        self,
        *,
        data: Iterable[Dict[str, object]],
        mode: Literal["create", "create-or-update"],
        target_name: str,
        target_type: Literal["table", "core-table"],
        batch_insert_ok: bool | Omit = omit,
        collect_output: bool | Omit = omit,
        defaults: Optional[Dict[str, str]] | Omit = omit,
        dry_run: bool | Omit = omit,
        job_execution_id: Optional[str] | Omit = omit,
        job_name: Optional[str] | Omit = omit,
        params_to_match_for_update: Optional[SequenceNotStr[str]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ToolWriteResponse:
        """
        Write data to a Labric table with support for inserts and upserts.

        This endpoint allows you to create new records or update existing records in any
        user-defined table within your organization. All write operations are tracked
        with provenance information for data lineage.

        ## Modes

        - **create**: Insert new records. Use `batch_insert_ok=true` for bulk inserts
          with better performance.
        - **create-or-update**: Upsert operation. Finds existing records by
          `params_to_match_for_update` fields and updates them, or creates new records
          if no match is found.

        ## Default Values

        Use the `defaults` parameter to automatically populate fields:

        - `DATETIME_NOW`: Current timestamp
        - `UUID4`: Generate a new UUID

        ## Job Tracking

        Every write operation is associated with a job execution for provenance
        tracking. Provide `job_execution_id` to link to an existing job, or let the
        system create one automatically (optionally named via `job_name`).

        ## Response

        Returns an empty list by default for performance. Set `collect_output=true` to
        receive the full data of all written records in the response.

        Args:
          data: A list of records to write. Each record is a dictionary where keys are column
              names and values are the data to insert or update.

          mode: The write operation mode. 'create' inserts new records (fails if duplicates
              exist). 'create-or-update' finds existing records by params_to_match_for_update
              and updates them, or creates new records if no match is found.

          target_name: The name of the table to write data to. Must be an existing table in your
              organization.

          target_type: The type of target to write to. Use 'table' for user-defined Labric tables, or
              'core-table' for built-in system tables.

          batch_insert_ok: When true, enables bulk insertion for better performance. Only available in
              'create' mode. Cannot be used with 'create-or-update' mode.

          collect_output: When true, the response will include the full data of all written records. When
              false (default), returns an empty list for better performance.

          defaults:
              Default values to apply to all records. Supports special function names:
              'DATETIME_NOW' (current timestamp) and 'UUID4' (generate a new UUID). These
              defaults are applied before the record data, so explicit values in data will
              override defaults.

          dry_run: When true, validates the write operation without persisting any changes to the
              database. Useful for testing data before committing.

          job_execution_id: Optional ID of an existing job execution to associate this write operation with.
              If not provided, a new job execution will be created automatically.

          job_name: Name for the automatically created job when job_execution_id is not provided.
              Defaults to 'Off-Platform Manual Job' if not specified.

          params_to_match_for_update: List of field names used to identify existing records for updates. Required when
              mode is 'create-or-update'. The system will search for records matching these
              fields and update them if found, or create new records if not.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/v1/tools/write",
            body=await async_maybe_transform(
                {
                    "data": data,
                    "mode": mode,
                    "target_name": target_name,
                    "target_type": target_type,
                    "batch_insert_ok": batch_insert_ok,
                    "collect_output": collect_output,
                    "defaults": defaults,
                    "dry_run": dry_run,
                    "job_execution_id": job_execution_id,
                    "job_name": job_name,
                    "params_to_match_for_update": params_to_match_for_update,
                },
                tool_write_params.ToolWriteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ToolWriteResponse,
        )


class ToolsResourceWithRawResponse:
    def __init__(self, tools: ToolsResource) -> None:
        self._tools = tools

        self.read = to_raw_response_wrapper(
            tools.read,
        )
        self.write = to_raw_response_wrapper(
            tools.write,
        )


class AsyncToolsResourceWithRawResponse:
    def __init__(self, tools: AsyncToolsResource) -> None:
        self._tools = tools

        self.read = async_to_raw_response_wrapper(
            tools.read,
        )
        self.write = async_to_raw_response_wrapper(
            tools.write,
        )


class ToolsResourceWithStreamingResponse:
    def __init__(self, tools: ToolsResource) -> None:
        self._tools = tools

        self.read = to_streamed_response_wrapper(
            tools.read,
        )
        self.write = to_streamed_response_wrapper(
            tools.write,
        )


class AsyncToolsResourceWithStreamingResponse:
    def __init__(self, tools: AsyncToolsResource) -> None:
        self._tools = tools

        self.read = async_to_streamed_response_wrapper(
            tools.read,
        )
        self.write = async_to_streamed_response_wrapper(
            tools.write,
        )
