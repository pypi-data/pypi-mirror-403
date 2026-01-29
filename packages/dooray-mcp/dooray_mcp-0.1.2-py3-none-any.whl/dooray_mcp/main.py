from mcp.server.fastmcp import FastMCP

from dooray_mcp.tools.comment import register_comment_tools
from dooray_mcp.tools.task import register_task_tools
from dooray_mcp.utils.config import config


mcp = FastMCP("dooray-mcp")


def create_server() -> FastMCP:
    config.load()
    register_task_tools(mcp)
    register_comment_tools(mcp)
    return mcp


def main():
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
