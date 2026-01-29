# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["ChatSendMessageParams"]


class ChatSendMessageParams(TypedDict, total=False):
    function_response: Annotated[object, PropertyInfo(alias="functionResponse")]
    """
    Optional: The output from a tool function that the AI previously requested to be
    executed.
    """
