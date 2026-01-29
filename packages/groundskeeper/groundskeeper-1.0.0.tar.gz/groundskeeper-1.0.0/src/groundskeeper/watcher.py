import asyncio
from collections.abc import Callable
from pathlib import Path

from watchfiles import Change, awatch


async def watch_files(
    prd_path: Path,
    progress_path: Path,
    on_prd_change: Callable[[], None],
    on_progress_change: Callable[[], None],
    stop_event: asyncio.Event,
) -> None:
    watch_dir = prd_path.parent

    async for changes in awatch(watch_dir, stop_event=stop_event):
        for change_type, path in changes:
            if change_type == Change.modified:
                if path == str(prd_path):
                    on_prd_change()
                elif path == str(progress_path):
                    on_progress_change()
