# dkist_inventory/frame_parsing.py

from typing import Any
from typing import Mapping

import numpy as np
from pydantic import BaseModel
from pydantic import Field


class InputFrameMetadata(BaseModel):
    """Represent a single input frame metadata bundle.

    Examples
    --------
    A raw JSON item looks like::

        {
          "bucket": "raw",
          "object_keys": ["...fits", "...fits", ...]
        }
    """

    bucket: str = Field(...)
    object_keys: list[str] = Field(default_factory=list)

    def to_asdf_friendly_structure(self) -> Mapping[str, Any]:
        """Convert this model into the structure stored in ASDF.

        Returns
        -------
        Mapping[str, Any]
            A mapping with ``bucket`` as a string and ``object_keys`` as a NumPy array
            of fixed-length ASCII bytes.
        """
        return {
            "bucket": self.bucket,
            "object_keys": np.asarray(self.object_keys, dtype="S"),
        }


class InputFramesParser(BaseModel):
    """Validate and convert input frame metadata documents for ASDF."""

    frames: list[InputFrameMetadata] = Field(default_factory=list)

    @classmethod
    def from_documents(
        cls, documents: list[Mapping[str, str | list[str]]] | None
    ) -> "InputFramesParser":
        """Parse and validate frame metadata documents.

        Parameters
        ----------
        documents
            A list of decoded JSON items. Each item is expected to include a ``bucket``
            string and an ``object_keys`` list of strings.

        Returns
        -------
        FrameParser
            A parser instance containing validated ``InputFrameMetadata`` items.
        """
        if not documents:
            return cls(frames=[])
        return cls(frames=[InputFrameMetadata(**doc) for doc in documents])

    @property
    def asdf_frame_metadata(self) -> list[Mapping[str, Any]]:
        """Return frames in the representation stored in ASDF.

        Returns
        -------
        list[Mapping[str, Any]]
            One mapping per input frame bundle. Any is expected to be a string or NumPy array.
        """
        return [frame.to_asdf_friendly_structure() for frame in self.frames]
