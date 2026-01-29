from mcp.server.fastmcp import FastMCP

from dooray_mcp.controllers import task as task_controller


def register_task_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="dooray_list_tasks",
        description="List tasks from Dooray project with optional filtering",
    )
    async def dooray_list_tasks(
        project_id: str,
        page: int = 0,
        size: int = 20,
        workflow_class: str | None = None,
        to_member_ids: str | None = None,
        tag_ids: str | None = None,
        milestone_ids: str | None = None,
        due_date: str | None = None,
        order: str = "-createdAt",
    ) -> str:
        result = await task_controller.list_tasks(
            project_id=project_id,
            page=page,
            size=size,
            workflow_class=workflow_class,
            to_member_ids=to_member_ids,
            tag_ids=tag_ids,
            milestone_ids=milestone_ids,
            due_date=due_date,
            order=order,
        )
        return result.content

    @mcp.tool(
        name="dooray_get_task",
        description="Get detailed information about a specific task",
    )
    async def dooray_get_task(
        project_id: str,
        post_id: str,
    ) -> str:
        result = await task_controller.get_task(
            project_id=project_id,
            post_id=post_id,
        )
        return result.content
