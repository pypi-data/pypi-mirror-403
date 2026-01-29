# Dooray MCP Server

MCP server for Dooray task and calendar integration.

## Features

- List tasks with filtering (workflow, assignee, milestone, etc.)
- Get task details
- List, add, update, delete comments

## Installation

```bash
pip install -e .
```

## Configuration

Create a `.env` file:

```env
DOORAY_API_KEY=your-api-key
DOORAY_PROJECT_ID=your-default-project-id
```

## Usage

### MCP Server (for Claude Desktop, Cursor, etc.)

```json
{
  "mcpServers": {
    "dooray": {
      "command": "dooray-mcp"
    }
  }
}
```

### CLI

```bash
# List tasks
dooray task list --project-id YOUR_PROJECT_ID
dooray task list --workflow working

# Get task details
dooray task get TASK_ID

# Comments
dooray comment list TASK_ID
dooray comment add TASK_ID --content "Your comment"
dooray comment update TASK_ID COMMENT_ID --content "Updated"
dooray comment delete TASK_ID COMMENT_ID
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `dooray_list_tasks` | List tasks with filtering |
| `dooray_get_task` | Get task details |
| `dooray_list_comments` | List comments |
| `dooray_add_comment` | Add comment |
| `dooray_update_comment` | Update comment |
| `dooray_delete_comment` | Delete comment |

## Development

```bash
pip install -e ".[dev]"
pytest
```
