# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["OAuthAuthorizeParams"]


class OAuthAuthorizeParams(TypedDict, total=False):
    client_id: Required[str]
    """Your client ID"""

    redirect_uri: Required[str]
    """Should match one of your configured redirect endpoints"""

    response_type: Required[Literal["code"]]
    """OAuth response type"""

    scope: Required[str]
    """Space delimited scopes being requested"""

    state: Required[str]
    """Opaque value passed back in the redirect"""
