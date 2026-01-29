from pydantic import BaseModel, Field


class TaskUser(BaseModel):
    type: str | None = None
    member: dict | None = None


class TaskWorkflow(BaseModel):
    id: str | None = None
    name: str | None = None

    model_config = {"extra": "ignore"}


class TaskMilestone(BaseModel):
    id: str | None = None
    name: str | None = None


class Task(BaseModel):
    id: str
    subject: str
    parent_post_id: str | None = Field(default=None, alias="parentPostId")
    workflow: TaskWorkflow | None = None
    milestone: TaskMilestone | None = None
    users: dict | None = None
    created_at: str | None = Field(default=None, alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")
    due_date: str | None = Field(default=None, alias="dueDate")

    model_config = {"populate_by_name": True, "extra": "ignore"}


class TaskDetail(Task):
    body: dict | None = None
    tags: list[dict] | None = None
    priority: str | None = None

    model_config = {"populate_by_name": True, "extra": "ignore"}


class TaskListResult(BaseModel):
    total_count: int = Field(alias="totalCount")
    contents: list[Task] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ListTasksParams(BaseModel):
    page: int = 0
    size: int = 20
    workflow_class: str | None = None
    to_member_ids: str | None = None
    tag_ids: str | None = None
    milestone_ids: str | None = None
    due_date: str | None = None
    order: str = "-createdAt"
