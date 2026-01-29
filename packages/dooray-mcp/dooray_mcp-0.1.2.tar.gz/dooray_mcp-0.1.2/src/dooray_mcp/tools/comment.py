from mcp.server.fastmcp import FastMCP

from dooray_mcp.controllers import comment as comment_controller


def register_comment_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="dooray_list_comments",
        description="List comments on a specific task",
    )
    async def dooray_list_comments(
        project_id: str,
        post_id: str,
    ) -> str:
        result = await comment_controller.list_comments(
            project_id=project_id,
            post_id=post_id,
        )
        return result.content

    @mcp.tool(
        name="dooray_add_comment",
        description="Add a new comment to a task",
    )
    async def dooray_add_comment(
        project_id: str,
        post_id: str,
        content: str,
    ) -> str:
        result = await comment_controller.add_comment(
            project_id=project_id,
            post_id=post_id,
            content=content,
        )
        return result.content

    @mcp.tool(
        name="dooray_update_comment",
        description="Update an existing comment",
    )
    async def dooray_update_comment(
        project_id: str,
        post_id: str,
        log_id: str,
        content: str,
    ) -> str:
        result = await comment_controller.update_comment(
            project_id=project_id,
            post_id=post_id,
            log_id=log_id,
            content=content,
        )
        return result.content

    @mcp.tool(
        name="dooray_delete_comment",
        description="Delete a comment from a task",
    )
    async def dooray_delete_comment(
        project_id: str,
        post_id: str,
        log_id: str,
    ) -> str:
        result = await comment_controller.delete_comment(
            project_id=project_id,
            post_id=post_id,
            log_id=log_id,
        )
        return result.content
