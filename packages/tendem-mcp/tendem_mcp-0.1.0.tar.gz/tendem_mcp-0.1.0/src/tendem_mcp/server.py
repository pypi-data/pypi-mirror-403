"""Tendem MCP server."""

import os
from functools import cache
from pathlib import Path
from uuid import UUID

from fastmcp import FastMCP

from tendem_mcp.client import TendemAPIError, TendemClient
from tendem_mcp.models import McpTaskListView, McpTaskResultsView, McpTaskView

mcp = FastMCP('tendem-mcp')

DEFAULT_API_URL = 'https://tendem.ai/api/v0'


@cache
def get_client() -> TendemClient:
    """Get or create the cached Tendem client."""
    api_key = os.environ.get('TENDEM_API_KEY')
    if not api_key:
        raise ValueError('TENDEM_API_KEY environment variable is required')
    base_url = os.environ.get('TENDEM_API_URL', DEFAULT_API_URL)
    debug = os.environ.get('TENDEM_DEBUG', '').lower() in ('1', 'true', 'yes')
    return TendemClient(api_key=api_key, base_url=base_url, debug=debug)


@mcp.tool
async def list_tasks(page_number: int, page_size: int) -> McpTaskListView | str:
    """List all tasks for the current user.

    Args:
        page_number: Page number (0-indexed).
        page_size: Number of results per page (1-100).

    Returns:
        Paginated list of tasks.
    """
    try:
        return await get_client().list_tasks(page_number, page_size)
    except TendemAPIError as e:
        return f'Error: {e}'


@mcp.tool
async def create_task(text: str) -> McpTaskView | str:
    """Create a new Tendem task with the given text.

    Args:
        text: The task description/prompt to execute.

    Returns:
        The created task.
    """
    try:
        return await get_client().create_task(text)
    except TendemAPIError as e:
        return f'Error: {e}'


@mcp.tool
async def get_task(task_id: str) -> McpTaskView | str:
    """Get a task by ID.

    Args:
        task_id: The task ID (UUID) to get.

    Returns:
        The task including status and approval info if awaiting approval.
    """
    try:
        return await get_client().get_task(UUID(task_id))
    except TendemAPIError as e:
        return f'Error: {e}'


@mcp.tool
async def approve_task(task_id: str) -> str:
    """Approve a task that is awaiting approval.

    Args:
        task_id: The task ID (UUID) to approve.

    Returns:
        Confirmation message.
    """
    try:
        await get_client().approve_task(UUID(task_id))
        return f'Task {task_id} approved'
    except TendemAPIError as e:
        return f'Error: {e}'


@mcp.tool
async def cancel_task(task_id: str) -> str:
    """Cancel a task.

    Args:
        task_id: The task ID (UUID) to cancel.

    Returns:
        Confirmation message.
    """
    try:
        await get_client().cancel_task(UUID(task_id))
        return f'Task {task_id} cancelled'
    except TendemAPIError as e:
        return f'Error: {e}'


@mcp.tool
async def get_task_results(
    task_id: str,
    page_number: int,
    page_size: int,
) -> McpTaskResultsView | str:
    """Get the results (published canvases) for a completed task.

    Args:
        task_id: The task ID (UUID) to get results for.
        page_number: Page number (0-indexed).
        page_size: Number of results per page (1-100).

    Returns:
        Paginated task results with canvas content.
    """
    try:
        return await get_client().get_task_results(UUID(task_id), page_number, page_size)
    except TendemAPIError as e:
        return f'Error: {e}'


@mcp.tool
async def download_artifact(task_id: str, artifact_id: str, path: str) -> str:
    """Download artifact content and save to a file.

    Args:
        task_id: The task ID (UUID).
        artifact_id: The artifact ID (UUID).
        path: The file path where the artifact should be saved.

    Returns:
        Confirmation message with the saved file path and size.
    """
    try:
        content = await get_client().get_artifact(UUID(task_id), artifact_id)
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        _ = file_path.write_bytes(content)
        size = len(content)
        if size < 1024:
            size_str = f'{size} bytes'
        elif size < 1024 * 1024:
            size_str = f'{size / 1024:.1f} KB'
        else:
            size_str = f'{size / (1024 * 1024):.1f} MB'
        return f'Artifact saved to {file_path} ({size_str})'
    except TendemAPIError as e:
        return f'Error: {e}'
    except OSError as e:
        return f'Error writing file: {e}'
