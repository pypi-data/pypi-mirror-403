from dooray_mcp.services.client import dooray_client
from dooray_mcp.types.comment import Comment, CommentListResult


async def list_comments(project_id: str, post_id: str) -> CommentListResult:
    path = f"/project/v1/projects/{project_id}/posts/{post_id}/logs"
    response = await dooray_client.get(path)
    result = response.get("result", [])

    if isinstance(result, list):
        total_count = response.get("header", {}).get("totalCount", len(result))
        return CommentListResult(totalCount=total_count, contents=result)

    return CommentListResult.model_validate(result)


async def add_comment(project_id: str, post_id: str, content: str) -> Comment:
    path = f"/project/v1/projects/{project_id}/posts/{post_id}/logs"
    body = {
        "body": {
            "mimeType": "text/x-markdown",
            "content": content,
        }
    }
    response = await dooray_client.post(path, json_data=body)
    return Comment.model_validate(response.get("result", {}))


async def update_comment(
    project_id: str, post_id: str, log_id: str, content: str
) -> Comment:
    path = f"/project/v1/projects/{project_id}/posts/{post_id}/logs/{log_id}"
    body = {
        "body": {
            "mimeType": "text/x-markdown",
            "content": content,
        }
    }
    response = await dooray_client.put(path, json_data=body)
    return Comment.model_validate(response.get("result", {}))


async def delete_comment(project_id: str, post_id: str, log_id: str) -> bool:
    path = f"/project/v1/projects/{project_id}/posts/{post_id}/logs/{log_id}"
    await dooray_client.delete(path)
    return True
