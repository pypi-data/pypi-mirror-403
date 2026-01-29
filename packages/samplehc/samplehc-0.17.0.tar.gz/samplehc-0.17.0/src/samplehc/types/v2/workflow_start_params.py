# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["WorkflowStartParams"]


class WorkflowStartParams(TypedDict, total=False):
    body: object
    """The workflow input data.

    Format depends on X-Sample-Start-Data-Parse-Method header: If 'standard'
    (default), wrap your data in a 'startData' key: { "startData": { ... } }. If
    'top-level', provide your data directly at the root level: { ... }. For
    multipart/form-data requests, include fields and files directly in the form
    data.
    """

    x_sample_start_data_parse_method: Annotated[
        Literal["standard", "top-level"], PropertyInfo(alias="X-Sample-Start-Data-Parse-Method")
    ]
