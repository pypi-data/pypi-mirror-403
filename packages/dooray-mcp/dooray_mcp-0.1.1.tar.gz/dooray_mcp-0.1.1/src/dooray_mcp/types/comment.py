from pydantic import BaseModel, Field


class CommentBody(BaseModel):
    mime_type: str = Field(default="text/x-markdown", alias="mimeType")
    content: str

    model_config = {"populate_by_name": True, "extra": "ignore"}


class Comment(BaseModel):
    id: str
    body: CommentBody | None = None
    created_at: str | None = Field(default=None, alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")

    model_config = {"populate_by_name": True, "extra": "ignore"}


class CommentListResult(BaseModel):
    total_count: int = Field(default=0, alias="totalCount")
    contents: list[Comment] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
