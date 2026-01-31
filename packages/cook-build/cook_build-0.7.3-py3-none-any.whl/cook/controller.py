import asyncio
import hashlib
import logging
import warnings
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection
from typing import (
    TYPE_CHECKING,
    Sequence,
    cast,
    overload,
)

import networkx as nx

from . import util

if TYPE_CHECKING:
    from .task import Task


LOGGER = logging.getLogger(__name__)
QUERIES = {
    "schema": """
    -- Information about the status of tasks.
    CREATE TABLE IF NOT EXISTS "tasks" (
        "name" TEXT PRIMARY KEY,
        "digest" TEXT NOT NULL,
        "last_completed" TIMESTAMP,
        "last_failed" TIMESTAMP,
        "last_started" TIMESTAMP
    );

    -- Information about files so we can cache digests.
    CREATE TABLE IF NOT EXISTS "files" (
        "name" TEXT PRIMARY KEY,
        "digest" TEXT NOT NULL,
        "last_digested" TIMESTAMP NOT NULL
    );
    """,
    "upsert_task_completed": """
        INSERT INTO "tasks" ("name", "digest", "last_completed")
        VALUES (:name, :digest, :last_completed)
        ON CONFLICT ("name") DO UPDATE SET "digest" = :digest, last_completed = :last_completed
    """,
    "upsert_task_failed": """
        INSERT INTO "tasks" ("name", "digest", "last_failed")
        VALUES (:name, '__failed__', :last_failed)
        ON CONFLICT ("name") DO UPDATE SET "digest" = '__failed__', last_failed = :last_failed
    """,
    "upsert_task_started": """
        INSERT INTO "tasks" ("name", "digest", "last_started")
        VALUES (:name, '__pending__', :last_started)
        ON CONFLICT ("name") DO UPDATE SET "digest" = '__pending__', last_started = :last_started
    """,
    "upsert_file": """
        INSERT INTO "files" ("name", "digest", "last_digested")
        VALUES (:name, :digest, :last_digested)
        ON CONFLICT ("name") DO UPDATE SET "digest" = :digest, last_digested = :last_digested
    """,
    "select_file": """
        SELECT "digest", "last_digested"
        FROM "files"
        WHERE "name" = :name AND last_digested > :last_modified
    """,
}


class Controller:
    """
    Controller to manage dependencies and execute tasks.
    """

    def __init__(self, dependencies: nx.DiGraph, connection: Connection) -> None:
        self.dependencies = dependencies
        self.connection = connection

    def resolve_stale_tasks(self, tasks: list["Task"] | None = None) -> set["Task"]:
        self.is_stale(tasks or list(self.dependencies))
        return {
            node for node, data in self.dependencies.nodes(True) if data.get("is_stale")
        }

    def _evaluate_task_hexdigest(self, task: "Task") -> str:
        """
        Evaluate the digest of a task by combining the digest of all its dependencies.
        """
        dependencies = []
        for dependency in task.dependencies:
            # Dependencies should be Path or str after normalize_dependencies runs.
            # Tasks should have been moved to task_dependencies.
            assert isinstance(dependency, (Path, str)), (
                f"Unexpected dependency type '{type(dependency)}'. Dependencies "
                "should be 'Path' or 'str' after 'normalize_dependencies'."
            )
            dependency = Path(dependency).resolve()
            if not dependency.is_file():
                raise FileNotFoundError(f"dependency {dependency} of {task} is missing")
            dependencies.append(dependency)

        hasher = hashlib.sha1()
        for dependency in sorted(dependencies):
            hasher.update(bytearray.fromhex(self._evaluate_path_hexdigest(dependency)))

        # Add the hash of the action.
        if task.action and (hexdigest := task.action.hexdigest):
            hasher.update(bytearray.fromhex(hexdigest))
        return hasher.hexdigest()

    def _evaluate_path_hexdigest(self, path: Path | str) -> str:
        """
        Get the digest of a file.
        """
        # Try to return the cached digest.
        path = Path(path)
        stat = path.stat()
        name = str(path.resolve())
        params = {"name": name, "last_modified": datetime.fromtimestamp(stat.st_mtime)}
        digest = self.connection.execute(QUERIES["select_file"], params).fetchone()
        if digest:
            return digest[0]

        # Evaluate a new digest and cache it.
        digest = util.evaluate_hexdigest(path)
        params = {
            "name": name,
            "last_digested": datetime.now(),
            "digest": digest,
        }
        self.connection.execute(QUERIES["upsert_file"], params)
        self.connection.commit()
        return digest

    @overload
    def is_stale(self, task: Sequence["Task"]) -> list[bool]: ...

    @overload
    def is_stale(self, task: "Task") -> bool: ...

    def is_stale(self, task: "Task | Sequence[Task]") -> bool | list[bool]:
        """
        Determine if one or more tasks are stale.

        Args:
            task: Task or tasks to check.

        Returns:
            If the task or tasks are stale.
        """
        if isinstance(task, Sequence):
            return [self.is_stale(x) for x in task]

        is_stale = self.dependencies.nodes[task].get("is_stale")
        if is_stale is not None:
            return is_stale
        is_stale = self._is_self_stale(task)
        successors = list(self.dependencies.successors(task))
        if successors:
            is_stale |= any(self.is_stale(successors))
        self.dependencies.nodes[task]["is_stale"] = is_stale
        return is_stale

    def _is_self_stale(self, task: "Task") -> bool:
        """
        Determine whether a task is *itself* stale irrespective of other tasks it may depend on.

        Args:
            task: Task to check.

        Returns:
            If the task is stale, ignoring dependencies.
        """
        # If there are no targets or the targets are missing, the task is stale.
        if not task.targets:
            LOGGER.debug("%s is stale because it has no targets", task)
            return True
        for target in task.targets:
            if not target.is_file():
                LOGGER.debug(
                    "%s is stale because its target `%s` is missing", task, target
                )
                return True

        # If there is no digest in the database, the task is stale.
        cached_digest = self.connection.execute(
            "SELECT digest FROM tasks WHERE name = :name", {"name": task.name}
        ).fetchone()
        if cached_digest is None:
            LOGGER.debug("%s is stale because it does not have a hash entry", task)
            return True

        # If one of the dependencies is missing, the task is stale.
        try:
            current_digest = self._evaluate_task_hexdigest(task)
        except FileNotFoundError:
            LOGGER.debug("%s is stale because one of its dependencies is missing", task)
            return True

        # If the digest has changed, the task is stale.
        (cached_digest,) = cached_digest
        if current_digest != cached_digest:
            LOGGER.debug(
                "%s is stale because one of its dependencies has changed (cached digest: "
                "%s, current digest: %s)",
                task,
                cached_digest,
                current_digest,
            )
            return True

        LOGGER.debug("%s is up to date", task)
        return False

    async def execute(
        self,
        tasks: "Task | list[Task]",
        num_concurrent: int = 1,
        interval: float | None = None,
        dry_run: bool = False,
    ) -> None:
        """
        Execute one or more tasks asynchronously.

        Args:
            tasks: Tasks to execute.
            num_concurrent: Number of concurrent tasks to run.
            interval: Deprecated, kept for backward compatibility.
            dry_run: If True, show what would execute without running tasks.
        """
        if interval is not None:  # pragma: no cover
            warnings.warn(
                "The 'interval' parameter is deprecated and has no effect",
                DeprecationWarning,
                stacklevel=2,
            )
        if not isinstance(tasks, Sequence):
            tasks = [tasks]
        if not any(self.is_stale(tasks)):
            return

        # Get the subgraph of stale nodes.
        stale_nodes = [
            node
            for node, data in self.dependencies.nodes.data()
            if data.get("is_stale")
        ]
        dependencies = cast(nx.DiGraph, self.dependencies.subgraph(stale_nodes).copy())

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(num_concurrent)

        # Create futures for all stale tasks
        task_futures: dict["Task", asyncio.Task] = {}
        for task in dependencies:
            task_futures[task] = asyncio.create_task(
                self._execute_task(task, task_futures, dependencies, semaphore, dry_run)
            )

        # Wait for requested tasks
        requested_futures = [task_futures[t] for t in tasks if t in task_futures]
        try:
            await asyncio.gather(*requested_futures)
        except Exception:
            # Cancel all pending tasks
            for future in task_futures.values():
                if not future.done():
                    future.cancel()
            # Wait for all cancellations to complete
            await asyncio.gather(*task_futures.values(), return_exceptions=True)
            raise

    async def _execute_task(
        self,
        task: "Task",
        task_futures: dict["Task", asyncio.Task],
        dependencies: nx.DiGraph,
        semaphore: asyncio.Semaphore,
        dry_run: bool,
    ) -> None:
        """Execute a single task after waiting for its dependencies."""
        # Wait for all dependencies to complete
        dep_tasks = list(dependencies.successors(task))
        if dep_tasks:
            dep_futures = [task_futures[dep] for dep in dep_tasks]
            await asyncio.gather(*dep_futures)

        digest: str | None = None
        if not dry_run:
            digest = self._evaluate_task_hexdigest(task)
        start: datetime | None = None

        try:
            # Log what we're doing
            if dry_run:
                LOGGER.log(
                    logging.DEBUG if task.name.startswith("_") else logging.INFO,
                    "would execute %s",
                    task,
                )
                if task.action:
                    LOGGER.log(
                        logging.DEBUG if task.name.startswith("_") else logging.INFO,
                        "  action: %s",
                        task.action,
                    )

            # Execute the task
            if not dry_run:
                async with semaphore:
                    start = datetime.now()
                    LOGGER.log(
                        logging.DEBUG if task.name.startswith("_") else logging.INFO,
                        "executing %s ...",
                        task,
                    )
                    params = {"name": task.name, "last_started": start}
                    self.connection.execute(QUERIES["upsert_task_started"], params)
                    self.connection.commit()
                    await task.execute()

                # Check that all targets were created
                for target in task.targets:
                    if not target.is_file():
                        raise FileNotFoundError(
                            f"task {task} did not create target {target}"
                        )
                    LOGGER.debug("%s created `%s`", task, target)

            # Update DB for completion
            if not dry_run:
                assert digest is not None
                params = {
                    "name": task.name,
                    "digest": digest,
                    "last_completed": datetime.now(),
                }
                self.connection.execute(QUERIES["upsert_task_completed"], params)
                self.connection.commit()

                # Log completion
                assert start is not None
                delta = util.format_timedelta(datetime.now() - start)
                LOGGER.log(
                    logging.DEBUG if task.name.startswith("_") else logging.INFO,
                    "completed %s in %s",
                    task,
                    delta,
                )

            # Mark task as no longer stale
            self.dependencies.nodes[task]["is_stale"] = False

        except Exception as ex:
            # Update DB for failure
            if not dry_run:
                params = {"name": task.name, "last_failed": datetime.now()}
                self.connection.execute(QUERIES["upsert_task_failed"], params)
                self.connection.commit()

            delta = util.format_timedelta(datetime.now() - start) if start else "?"
            LOGGER.exception("failed to execute %s after %s", task, delta)
            raise util.FailedTaskError(ex, task=task) from ex

    def reset(self, *tasks: "Task") -> None:
        # TODO: add tests for resetting.
        params = [{"name": task.name} for task in tasks]
        cursor = self.connection.executemany(
            "UPDATE tasks SET digest = '__reset__' WHERE name = :name", params
        )
        self.connection.commit()
        n_reset = cursor.rowcount
        LOGGER.info("reset %d %s", n_reset, "task" if n_reset == 1 else "tasks")
