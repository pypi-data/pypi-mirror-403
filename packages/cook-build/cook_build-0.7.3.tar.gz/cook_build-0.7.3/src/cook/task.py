from __future__ import annotations

import asyncio
import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import colorama

from . import util

if TYPE_CHECKING:
    from .actions import Action
    from .util import PathOrStr


LOGGER = logging.getLogger(__name__)


class Task:
    """
    Task to be executed.
    """

    def __init__(
        self,
        name: str | None = None,
        *,
        dependencies: list["PathOrStr | Task"] | None = None,
        targets: list["PathOrStr"] | None = None,
        action: Action | None = None,
        task_dependencies: list[Task] | None = None,
        location: tuple[str, int] | None = None,
    ) -> None:
        self.dependencies = dependencies or []
        self.targets = [Path(path) for path in (targets or [])]
        if name is None:
            if not self.targets:
                raise ValueError("'name' is required if there are no targets.")
            name = str(self.targets[0])
        self.name = name
        self.action = action
        self.task_dependencies = task_dependencies or []
        self.location = location or util.get_location()

    async def execute(self) -> None:
        if self.action:
            # Check if the action's execute method is actually async
            # This handles custom actions that may have implemented sync execute()
            if inspect.iscoroutinefunction(self.action.execute):
                await self.action.execute(self)
            else:
                # User implemented old-style sync execute() - run in executor with warning
                LOGGER.warning(
                    f"{self.action.__class__.__name__} implements sync execute(); "
                    "please update to async def execute() for better performance"
                )
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.action.execute, self)

    def __hash__(self) -> int:
        return hash(self.name)

    def format(self, color: str | None = None) -> str:
        name = self.name
        if color:
            name = f"{color}{name}{colorama.Fore.RESET}"
        filename, lineno = self.location
        return f"<task `{name}` @ {filename}:{lineno}>"

    def __repr__(self) -> str:
        return self.format()
