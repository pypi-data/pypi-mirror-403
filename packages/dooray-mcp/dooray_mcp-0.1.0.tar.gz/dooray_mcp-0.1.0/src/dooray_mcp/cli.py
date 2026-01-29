import asyncio

import typer
from rich.console import Console

from dooray_mcp.controllers import comment as comment_controller
from dooray_mcp.controllers import task as task_controller
from dooray_mcp.utils.config import config
from dooray_mcp.utils.errors import DoorayError


app = typer.Typer(name="dooray", help="Dooray CLI")
task_app = typer.Typer(name="task", help="Task commands")
comment_app = typer.Typer(name="comment", help="Comment commands")

app.add_typer(task_app)
app.add_typer(comment_app)

console = Console()


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def handle_error(e: Exception):
    if isinstance(e, DoorayError):
        console.print(f"[red]Error: {e}[/red]")
    else:
        console.print(f"[red]Unexpected error: {e}[/red]")
    raise typer.Exit(1)


@task_app.command("list")
def list_tasks(
    project_id: str = typer.Option(..., "--project-id", "-p"),
    page: int = typer.Option(0, "--page"),
    size: int = typer.Option(20, "--size"),
    workflow: str | None = typer.Option(None, "--workflow", "-w"),
    order: str = typer.Option("-createdAt", "--order"),
):
    config.load()
    try:
        result = run_async(
            task_controller.list_tasks(
                project_id=project_id,
                page=page,
                size=size,
                workflow_class=workflow,
                order=order,
            )
        )
        console.print(result.content)
    except Exception as e:
        handle_error(e)


@task_app.command("get")
def get_task(
    post_id: str = typer.Argument(..., help="Task ID"),
    project_id: str = typer.Option(..., "--project-id", "-p"),
):
    config.load()
    try:
        result = run_async(
            task_controller.get_task(project_id=project_id, post_id=post_id)
        )
        console.print(result.content)
    except Exception as e:
        handle_error(e)


@comment_app.command("list")
def list_comments(
    post_id: str = typer.Argument(..., help="Task ID"),
    project_id: str = typer.Option(..., "--project-id", "-p"),
):
    config.load()
    try:
        result = run_async(
            comment_controller.list_comments(project_id=project_id, post_id=post_id)
        )
        console.print(result.content)
    except Exception as e:
        handle_error(e)


@comment_app.command("add")
def add_comment(
    post_id: str = typer.Argument(..., help="Task ID"),
    content: str = typer.Option(..., "--content", "-c", help="Comment content"),
    project_id: str = typer.Option(..., "--project-id", "-p"),
):
    config.load()
    try:
        result = run_async(
            comment_controller.add_comment(
                project_id=project_id, post_id=post_id, content=content
            )
        )
        console.print(f"[green]{result.content}[/green]")
    except Exception as e:
        handle_error(e)


@comment_app.command("update")
def update_comment(
    post_id: str = typer.Argument(..., help="Task ID"),
    log_id: str = typer.Argument(..., help="Comment ID"),
    content: str = typer.Option(..., "--content", "-c", help="New content"),
    project_id: str = typer.Option(..., "--project-id", "-p"),
):
    config.load()
    try:
        result = run_async(
            comment_controller.update_comment(
                project_id=project_id, post_id=post_id, log_id=log_id, content=content
            )
        )
        console.print(f"[green]{result.content}[/green]")
    except Exception as e:
        handle_error(e)


@comment_app.command("delete")
def delete_comment(
    post_id: str = typer.Argument(..., help="Task ID"),
    log_id: str = typer.Argument(..., help="Comment ID"),
    project_id: str = typer.Option(..., "--project-id", "-p"),
):
    config.load()
    try:
        result = run_async(
            comment_controller.delete_comment(
                project_id=project_id, post_id=post_id, log_id=log_id
            )
        )
        console.print(f"[green]{result.content}[/green]")
    except Exception as e:
        handle_error(e)


if __name__ == "__main__":
    app()
