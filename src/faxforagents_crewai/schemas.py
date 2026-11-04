"""REST request shapes restricted to the canonical tool surface."""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

DocumentId = Annotated[str, Field(pattern=r"^doc_[0-9a-f]{32}$")]
UploadId = Annotated[str, Field(pattern=r"^up_[0-9a-f]{32}$")]
QuoteId = Annotated[str, Field(pattern=r"^quote_[0-9a-f]{32}$")]
ApprovalId = Annotated[str, Field(pattern=r"^apr_[0-9a-f]{32}$")]
FaxId = Annotated[str, Field(pattern=r"^fax_[0-9a-f]{32}$")]
InboxId = Annotated[str, Field(pattern=r"^inb_[0-9a-f]{32}$")]
Text = Annotated[str, Field(min_length=1, max_length=200_000)]


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Mutation(Arguments):
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)] = Field(
        description="Caller-chosen token. Reuse the same token and payload on retries."
    )

    @field_validator("idempotency_key")
    @classmethod
    def valid_key(cls, value: str) -> str:
        if not value.strip() or any(ord(c) < 33 or ord(c) > 126 for c in value):
            raise ValueError("Use a nonblank visible ASCII retry token without spaces.")
        return value


class GetGuideInput(Arguments):
    section: str | None = None


class PrepareFaxInput(Mutation):
    text: Text | None = None
    markdown: Text | None = None
    html: Annotated[str, Field(min_length=1)] | None = None
    upload_id: UploadId | None = None
    filename: Annotated[str, Field(max_length=255)] | None = None

    @model_validator(mode="after")
    def one_source(self) -> PrepareFaxInput:
        sources = (self.text, self.markdown, self.html, self.upload_id)
        if sum(s is not None for s in sources) != 1:
            raise ValueError("Supply exactly one document source.")
        if any(s is not None and not s.strip() for s in sources):
            raise ValueError("Document content cannot be blank.")
        if self.html is not None and len(self.html.encode("utf-8")) > 2 * 1024 * 1024:
            raise ValueError("HTML exceeds two MiB of UTF-8.")
        return self


class GetFaxDocumentInput(Arguments):
    document_id: DocumentId


class Cover(Arguments):
    to_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = None
    from_name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None = (
        None
    )
    from_email: Annotated[str, StringConstraints(strip_whitespace=True, max_length=254)] | None = (
        None
    )
    subject: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None = None
    message: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] | None = None


class QuoteFaxInput(Mutation):
    document_id: DocumentId
    to: Annotated[str, Field(pattern=r"^\+[1-9][0-9]{1,14}$")]
    cover: Cover | None = None


class SendApprovedFaxInput(Mutation):
    quote_id: QuoteId
    approval_id: ApprovalId | None = Field(
        default=None,
        description="Human approval bound to this quote. Required for every live send.",
    )
    client_reference: Annotated[str, Field(max_length=200)] | None = None


class GetFaxStatusInput(Arguments):
    fax_id: FaxId


class PageInput(Arguments):
    limit: int = 20
    cursor: str | None = None

    @field_validator("limit")
    @classmethod
    def clamp_limit(cls, value: int) -> int:
        return max(1, min(100, value))


class ListFaxesInput(PageInput):
    state: Literal["queued", "active", "delivered", "partial", "failed", "unknown"] | None = None


class CancelFaxInput(Mutation):
    fax_id: FaxId


class RequestHumanReviewInput(Mutation):
    message: str
    quote_id: QuoteId | None = None
    fax_id: FaxId | None = None

    @model_validator(mode="after")
    def review_target(self) -> RequestHumanReviewInput:
        if self.quote_id and self.fax_id:
            raise ValueError("quote_id and fax_id are mutually exclusive.")
        if self.quote_id is None and not self.message.strip():
            raise ValueError("Help requests require a message.")
        self.message = self.message[:2000]
        return self


class GetReviewStatusInput(Arguments):
    review_request_id: ApprovalId


class ReadInboundFaxInput(Arguments):
    inbox_id: InboxId


class ExtractFaxDataInput(Mutation):
    inbox_item_id: InboxId | None = None
    document_id: DocumentId | None = None
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")
    strong_model_if_below: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] = 0.75

    @model_validator(mode="after")
    def extraction_shape(self) -> ExtractFaxDataInput:
        if (self.inbox_item_id is None) == (self.document_id is None):
            raise ValueError("Supply exactly one extraction source.")
        schema = self.schema_
        if schema is None:
            return self
        properties = schema.get("properties")
        if schema.get("type") != "object" or not isinstance(properties, dict):
            raise ValueError("Schema must describe an object with properties.")
        if not 1 <= len(properties) <= 50:
            raise ValueError("Schema must declare one to fifty fields.")
        for name, prop in properties.items():
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", name):
                raise ValueError("Invalid extraction field name.")
            if not isinstance(prop, dict) or prop.get("type") not in {
                "string",
                "number",
                "boolean",
                "date",
            }:
                raise ValueError("Unsupported extraction field type.")
            description = prop.get("description", "")
            if not isinstance(description, str) or len(description) > 500:
                raise ValueError("Invalid extraction field description.")
        required = schema.get("required", [])
        if not isinstance(required, list) or any(
            not isinstance(name, str) or name not in properties for name in required
        ):
            raise ValueError("Required fields must be declared properties.")
        return self
