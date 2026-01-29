# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["OAuthDeauthorizeParams"]


class OAuthDeauthorizeParams(TypedDict, total=False):
    token: Required[str]
    """An access token for the user to deauthorize"""

    client_id: Required[str]
    """Your client ID"""

    client_secret: Required[str]
    """Your client secret"""
