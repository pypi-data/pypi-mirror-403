# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

from ..._types import FileTypes

__all__ = ["FileUpdateParams"]


class FileUpdateParams(TypedDict, total=False):
    file: FileTypes
    """A route file.

    Filename should have one of the following extensions: .gpx .fit .tcx .kml .kmz
    """
