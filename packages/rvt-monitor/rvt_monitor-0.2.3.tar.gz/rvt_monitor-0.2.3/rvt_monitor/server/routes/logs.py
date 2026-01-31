"""Logs API routes."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from rvt_monitor.core.logger import get_log_files, read_log_file, export_logs_csv

router = APIRouter()


@router.get("")
async def list_logs():
    """Get list of log files."""
    files = get_log_files()
    return {"files": files}


@router.get("/{date}")
async def get_log(date: str, limit: int = 500, offset: int = 0):
    """Get log file contents for a specific date."""
    lines = read_log_file(date, limit=limit, offset=offset)
    return {
        "date": date,
        "lines": lines,
        "count": len(lines),
        "offset": offset,
    }


@router.get("/{date}/export")
async def export_log(date: str):
    """Export log file as CSV."""
    csv_content = export_logs_csv(date)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{date}.csv"'
        },
    )
