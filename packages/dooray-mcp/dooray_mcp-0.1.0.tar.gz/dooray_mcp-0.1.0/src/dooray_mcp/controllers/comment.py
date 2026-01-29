from dooray_mcp.services import comment_api
from dooray_mcp.types.common import ControllerResponse


async def list_comments(
    project_id: str,
    post_id: str,
) -> ControllerResponse:
    result = await comment_api.list_comments(project_id, post_id)

    if not result.contents:
        return ControllerResponse(content="No comments found.")

    lines = [f"Found {result.total_count} comments:\n"]

    for comment in result.contents:
        content = ""
        if comment.body:
            content = comment.body.content[:100]
            if len(comment.body.content) > 100:
                content += "..."

        lines.append(f"- **Comment ID**: {comment.id}")
        lines.append(f"  - Created: {comment.created_at or 'N/A'}")
        lines.append(f"  - Content: {content}")
        lines.append("")

    return ControllerResponse(content="\n".join(lines))


async def add_comment(
    project_id: str,
    post_id: str,
    content: str,
) -> ControllerResponse:
    comment = await comment_api.add_comment(project_id, post_id, content)
    return ControllerResponse(content=f"Comment added successfully. (ID: {comment.id})")


async def update_comment(
    project_id: str,
    post_id: str,
    log_id: str,
    content: str,
) -> ControllerResponse:
    comment = await comment_api.update_comment(project_id, post_id, log_id, content)
    return ControllerResponse(content=f"Comment updated successfully. (ID: {comment.id})")


async def delete_comment(
    project_id: str,
    post_id: str,
    log_id: str,
) -> ControllerResponse:
    await comment_api.delete_comment(project_id, post_id, log_id)
    return ControllerResponse(content=f"Comment deleted successfully. (ID: {log_id})")
