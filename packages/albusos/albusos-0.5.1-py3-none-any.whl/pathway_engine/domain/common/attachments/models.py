"""Attachment DTOs (core contract).

These are typed references/bindings that can be attached to an Agent run or a Copilot turn.
They intentionally avoid embedding full document/canvas content; the host/runtime is expected
to resolve them into concrete data when needed.
"""

from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class DocSelectionAttachment(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["doc_selection"] = "doc_selection"
    doc_id: str = Field(min_length=1)
    doc_name: str | None = None
    head_rev: str | None = None
    start: int | None = None
    end: int | None = None
    # Optional inline text (transport convenience; not a SSOT field)
    text: str | None = None


class CanvasSelectionAttachment(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["canvas_selection"] = "canvas_selection"
    doc_id: str = Field(min_length=1)
    shape_ids: list[str] = Field(default_factory=list)
    summary: str | None = None


class ImageAttachment(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Literal["image"] = "image"
    mime_type: str = "image/png"
    data_base64: str = Field(min_length=1)
    name: str | None = None


Attachment = Union[DocSelectionAttachment, CanvasSelectionAttachment, ImageAttachment]


def safe_parse_attachments(raw: Any) -> list[Attachment]:
    if not isinstance(raw, list):
        return []
    out: list[Attachment] = []
    for a in raw[:20]:
        if not isinstance(a, dict):
            continue
        at = str(a.get("type") or "").strip()
        try:
            if at == "doc_selection":
                out.append(DocSelectionAttachment.model_validate(a))
            elif at == "canvas_selection":
                out.append(CanvasSelectionAttachment.model_validate(a))
            elif at == "image":
                out.append(ImageAttachment.model_validate(a))
        except Exception:
            continue
    return out


__all__ = [
    "Attachment",
    "DocSelectionAttachment",
    "CanvasSelectionAttachment",
    "ImageAttachment",
    "safe_parse_attachments",
]
