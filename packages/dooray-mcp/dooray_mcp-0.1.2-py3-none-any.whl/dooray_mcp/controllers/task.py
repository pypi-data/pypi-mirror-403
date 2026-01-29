from dooray_mcp.services import task_api
from dooray_mcp.types.common import ControllerResponse
from dooray_mcp.types.task import ListTasksParams


async def list_tasks(
    project_id: str,
    page: int = 0,
    size: int = 20,
    workflow_class: str | None = None,
    to_member_ids: str | None = None,
    tag_ids: str | None = None,
    milestone_ids: str | None = None,
    due_date: str | None = None,
    order: str = "-createdAt",
) -> ControllerResponse:
    params = ListTasksParams(
        page=page,
        size=size,
        workflow_class=workflow_class,
        to_member_ids=to_member_ids,
        tag_ids=tag_ids,
        milestone_ids=milestone_ids,
        due_date=due_date,
        order=order,
    )

    result = await task_api.list_tasks(project_id, params)

    if not result.contents:
        return ControllerResponse(content="No tasks found.")

    lines = [f"Found {result.total_count} tasks:\n"]

    for task in result.contents:
        workflow_name = task.workflow.name if task.workflow else "N/A"
        due = task.due_date or "No due date"
        lines.append(f"- **{task.subject}** (ID: {task.id})")
        lines.append(f"  - Status: {workflow_name}")
        lines.append(f"  - Due: {due}")
        lines.append("")

    return ControllerResponse(content="\n".join(lines))


async def get_task(
    project_id: str,
    post_id: str,
) -> ControllerResponse:
    task = await task_api.get_task(project_id, post_id)

    workflow_name = task.workflow.name if task.workflow else "N/A"
    milestone_name = task.milestone.name if task.milestone else "N/A"
    due = task.due_date or "No due date"
    body_content = ""
    if task.body and "content" in task.body:
        body_content = task.body["content"]

    lines = [
        f"# {task.subject}",
        "",
        f"- **ID**: {task.id}",
        f"- **Status**: {workflow_name}",
        f"- **Milestone**: {milestone_name}",
        f"- **Priority**: {task.priority or 'N/A'}",
        f"- **Due**: {due}",
        f"- **Created**: {task.created_at or 'N/A'}",
        f"- **Updated**: {task.updated_at or 'N/A'}",
    ]

    if body_content:
        lines.extend(["", "## Description", "", body_content])

    return ControllerResponse(content="\n".join(lines))
