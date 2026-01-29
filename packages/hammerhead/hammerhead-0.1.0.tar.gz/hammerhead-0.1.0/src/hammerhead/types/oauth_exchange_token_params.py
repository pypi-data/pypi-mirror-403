# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["OAuthExchangeTokenParams"]


class OAuthExchangeTokenParams(TypedDict, total=False):
    client_id: Required[str]
    """Your client ID"""

    client_secret: Required[str]
    """Your client secret"""

    grant_type: Required[Literal["authorization_code", "refresh_token"]]
    """OAuth grant type"""

    code: str
    """Required for code auth, generated from initial authorize request"""

    redirect_uri: str
    """
    Required for code auth, should match the `redirect_uri` from the authorize
    request
    """

    refresh_token: str
    """Required for code auth, generated from previous token request"""
