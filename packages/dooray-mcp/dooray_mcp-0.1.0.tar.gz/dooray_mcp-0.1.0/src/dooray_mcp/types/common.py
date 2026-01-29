from typing import Any, Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class DoorayResponse(BaseModel, Generic[T]):
    header: dict[str, Any]
    result: T | None = None


class ControllerResponse(BaseModel):
    content: str
    success: bool = True
