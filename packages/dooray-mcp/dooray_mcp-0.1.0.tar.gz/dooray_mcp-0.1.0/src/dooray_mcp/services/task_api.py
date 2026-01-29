from typing import Any

from dooray_mcp.services.client import dooray_client
from dooray_mcp.types.task import ListTasksParams, TaskDetail, TaskListResult


async def list_tasks(project_id: str, params: ListTasksParams) -> TaskListResult:
    path = f"/project/v1/projects/{project_id}/posts"

    query_params: dict[str, Any] = {
        "page": params.page,
        "size": params.size,
        "order": params.order,
    }

    if params.workflow_class:
        query_params["postWorkflowClasses"] = params.workflow_class
    if params.to_member_ids:
        query_params["toMemberIds"] = params.to_member_ids
    if params.tag_ids:
        query_params["tagIds"] = params.tag_ids
    if params.milestone_ids:
        query_params["milestoneIds"] = params.milestone_ids
    if params.due_date:
        query_params["dueAt"] = params.due_date

    response = await dooray_client.get(path, params=query_params)
    result = response.get("result", [])

    if isinstance(result, list):
        total_count = response.get("header", {}).get("totalCount", len(result))
        return TaskListResult(totalCount=total_count, contents=result)

    return TaskListResult.model_validate(result)


async def get_task(project_id: str, post_id: str) -> TaskDetail:
    path = f"/project/v1/projects/{project_id}/posts/{post_id}"

    response = await dooray_client.get(path)
    return TaskDetail.model_validate(response.get("result", {}))
