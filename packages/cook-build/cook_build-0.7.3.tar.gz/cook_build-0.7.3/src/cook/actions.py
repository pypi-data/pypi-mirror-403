"""
Actions
-------

Actions are performed when tasks are executed. Builtin actions include calling python functions
using :class:`.FunctionAction`, running subprocesses using :class:`.SubprocessAction`, composing
multiple actions using :class:`.CompositeAction`, and executing modules as scripts using
:class:`.ModuleAction`.

Custom actions can be implemented by inheriting from :class:`.Action` and implementing the
:meth:`~.Action.execute` method which receives a :class:`~.task.Task`. The method should be async
and its return value is ignored. For example, the following action waits for a specified time.

.. doctest::

    >>> from cook.actions import Action
    >>> from cook.task import Task
    >>> import asyncio
    >>> from time import time

    >>> class SleepAction(Action):
    ...     def __init__(self, delay: float) -> None:
    ...         self.delay = delay
    ...
    ...     async def execute(self, task: Task) -> None:
    ...         start = time()
    ...         await asyncio.sleep(self.delay)
    ...         print(f"time: {time() - start:.3f}")

    >>> action = SleepAction(0.1)
    >>> asyncio.run(action.execute(None))
    time: 0.1...

For backwards compatibility, synchronous execute methods are also supported but will run in an
executor with a deprecation warning.
"""

import asyncio
import functools
import hashlib
import logging
import os
import shlex
import subprocess
import sys
from types import ModuleType
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .task import Task


LOGGER = logging.getLogger(__name__)


class Action:
    """
    Action to perform when a task is executed.
    """

    async def execute(self, task: "Task") -> None:
        """
        Execute the action asynchronously.
        """
        raise NotImplementedError

    @property
    def hexdigest(self) -> str | None:
        """
        Optional digest to check if an action changed.
        """
        return None


class FunctionAction(Action):
    """
    Action wrapping a python callable.

    Args:
        func: Function to call which must accept a :class:`~.task.Task` as its first argument.
        *args: Additional positional arguments.
        **kwargs: Keyword arguments.
    """

    def __init__(self, func: Callable, *args, **kwargs) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    async def execute(self, task: "Task") -> None:
        # Check if the function is already async
        if asyncio.iscoroutinefunction(self.func):
            await self.func(task, *self.args, **self.kwargs)
        else:
            # Run sync function in executor
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, functools.partial(self.func, task, *self.args, **self.kwargs)
            )


class SubprocessAction(Action):
    """
    Run a subprocess asynchronously.

    Args:
        *args: Positional arguments for subprocess execution.
        **kwargs: Keyword arguments for subprocess execution.

    Example:

        .. doctest::

            >>> from cook.actions import SubprocessAction
            >>> from pathlib import Path
            >>> import asyncio

            >>> action = SubprocessAction(["touch", "hello.txt"])
            >>> asyncio.run(action.execute(None))
            >>> Path("hello.txt").is_file()
            True
    """

    def __init__(self, args: str | list[str], **kwargs) -> None:
        # Validate shell argument early
        if kwargs.get("shell", False) and not isinstance(args, str):
            raise ValueError("shell=True requires string args")
        self.args = args
        self.kwargs = kwargs

    async def execute(self, task: "Task") -> None:
        # Get the command arguments
        args = self.args
        shell = self.kwargs.get("shell", False)
        other_kwargs = {k: v for k, v in self.kwargs.items() if k != "shell"}

        # Create the subprocess
        if shell:
            assert isinstance(args, str)
            process = await asyncio.create_subprocess_shell(args, **other_kwargs)
        else:
            # Exec mode: args can be a string (single command) or list
            if isinstance(args, str):
                # Single command string - treat as program name with no arguments
                process = await asyncio.create_subprocess_exec(args, **other_kwargs)
            else:
                # List of arguments
                process = await asyncio.create_subprocess_exec(*args, **other_kwargs)

        try:
            # Wait for the process to complete
            returncode = await process.wait()
            if returncode:
                raise subprocess.CalledProcessError(returncode, args)

        except asyncio.CancelledError:
            # Task was cancelled - terminate the subprocess
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=3)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            raise

    @property
    def hexdigest(self) -> str:
        hasher = hashlib.sha1()
        args = self.args
        if isinstance(args, str):
            hasher.update(args.encode())
        else:
            for arg in args:
                hasher.update(arg.encode())
        return hasher.hexdigest()

    def __repr__(self) -> str:
        args = self.args
        if not isinstance(args, str):
            args = " ".join(map(shlex.quote, args))
        return f"{self.__class__.__name__}({repr(args)})"


class CompositeAction(Action):
    """
    Execute multiple actions sequentially.

    Args:
        *actions: Actions to execute.
    """

    def __init__(self, *actions: Action) -> None:
        self.actions = actions

    async def execute(self, task: "Task") -> None:
        for action in self.actions:
            await action.execute(task)

    @property
    def hexdigest(self) -> str | None:
        hasher = hashlib.sha1()
        for action in self.actions:
            hexdigest = action.hexdigest
            if hexdigest is None:
                return None
            hasher.update(bytearray.fromhex(hexdigest))
        return hasher.hexdigest()


class ModuleAction(SubprocessAction):
    """
    Execute a module as a script.

    Args:
        args: List comprising the module to execute as the first element and arguments for the
            module as subsequent elements.
        debug: Run the module using `pdb` (defaults to the :code:`COOK_DEBUG` environment variable
            being set).
        **kwargs: Keyword arguments for :class:`subprocess.Popen`.
    """

    def __init__(self, args: list, debug: bool | None = None, **kwargs) -> None:
        if kwargs.get("shell"):
            raise ValueError("shell execution is not supported by `ModuleAction`")
        if not args:
            raise ValueError("`args` must not be empty")
        module: ModuleType
        module, *args = args
        if not isinstance(module, ModuleType):
            raise TypeError("first element of `args` must be a module")

        # Assemble the arguments.
        args_ = [sys.executable, "-m"]
        debug = "COOK_DEBUG" in os.environ if debug is None else debug
        if debug:
            args_.extend(["pdb", "-m"])
        args_.extend([module.__name__, *map(str, args)])
        super().__init__(args_, **kwargs)
