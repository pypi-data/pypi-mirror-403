import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from sqlite3 import Connection
from unittest.mock import patch

import pytest

from cook import Controller, Manager, Task
from cook.actions import Action, CompositeAction, FunctionAction, SubprocessAction
from cook.contexts import normalize_action, normalize_dependencies
from cook.controller import QUERIES
from cook.util import FailedTaskError, Timer


def touch(task: Task) -> None:
    for target in task.targets:
        target.write_text(target.name)


def test_controller_empty_task(m: Manager, conn: Connection) -> None:
    task = m.create_task("foo")
    c = Controller(m.resolve_dependencies(), conn)
    assert c.is_stale(task)
    assert c.resolve_stale_tasks() == {task}


def test_controller_missing_target(m: Manager, conn: Connection) -> None:
    task = m.create_task("foo", targets=["bar"])
    c = Controller(m.resolve_dependencies(), conn)
    assert c.is_stale(task)
    assert c.resolve_stale_tasks() == {task}


def test_controller_simple_file_deps(
    m: Manager, conn: Connection, tmp_wd: Path
) -> None:
    for path in ["input.txt", "output.txt"]:
        Path(path).write_text(path)
    with normalize_dependencies():
        task = m.create_task("foo", dependencies=["input.txt"], targets=["output.txt"])
    c = Controller(m.resolve_dependencies(), conn)

    # No entry in the database.
    assert c.is_stale(task)
    assert c.resolve_stale_tasks() == {task}

    # Up to date entry in the database.
    params = {
        "name": "foo",
        "digest": "80d4129af3d5366c3fcd26c498e143d9a199f7c4",
        "last_completed": None,
    }
    conn.execute(QUERIES["upsert_task_completed"], params)
    c = Controller(m.resolve_dependencies(), conn)
    assert not c.is_stale(task)

    # Wrong digest in the database.
    params = {"name": "foo", "digest": "-", "last_completed": None}
    conn.execute(QUERIES["upsert_task_completed"], params)
    c = Controller(m.resolve_dependencies(), conn)
    assert c.is_stale(task)


def test_controller_missing_input(m: Manager, conn: Connection) -> None:
    with normalize_dependencies():
        m.create_task("input", targets=["input.txt"], action=FunctionAction(touch))
        output = m.create_task(
            "output",
            targets=["output.txt"],
            action=FunctionAction(touch),
            dependencies=["input.txt"],
        )

    # Create the output.
    Path("output.txt").write_text("output.txt")
    params = {
        "name": "output",
        "digest": "80d4129af3d5366c3fcd26c498e143d9a199f7c4",
        "last_completed": None,
    }
    conn.execute(QUERIES["upsert_task_completed"], params)
    c = Controller(m.resolve_dependencies(), conn)
    assert c.is_stale(output) is True


@pytest.mark.asyncio
async def test_controller(m: Manager, conn: Connection) -> None:
    for filename in ["input1.txt", "input2.txt", "intermediate.txt", "output1.txt"]:
        Path(filename).write_text(filename)

    with normalize_dependencies():
        intermediate = m.create_task(
            "intermediate",
            dependencies=["input1.txt", "input2.txt"],
            targets=["intermediate.txt"],
            action=FunctionAction(touch),
        )
        output1 = m.create_task(
            "output1",
            dependencies=["intermediate.txt"],
            targets=["output1.txt"],
            action=FunctionAction(touch),
        )
        output2 = m.create_task(
            "output2",
            targets=["output2.txt"],
            action=FunctionAction(touch),
            dependencies=["intermediate.txt", "input2.txt", "output1.txt"],
        )
        special = m.create_task("special", dependencies=["intermediate.txt"])

    # We should get back all tasks at the beginning.
    c = Controller(m.resolve_dependencies(), conn)
    assert c.resolve_stale_tasks() == {intermediate, output1, output2, special}

    # Make sure we don't get any tasks that are upstream from what we request.
    c = Controller(m.resolve_dependencies(), conn)
    assert c.resolve_stale_tasks([output1]) == {intermediate, output1}

    # Execute tasks and check that they are no longer stale.
    c = Controller(m.resolve_dependencies(), conn)
    await c.execute(output1)
    assert not c.resolve_stale_tasks([output1])

    # But the other ones are still stale.
    c = Controller(m.resolve_dependencies(), conn)
    assert c.resolve_stale_tasks() == {output2, special}

    # Execute the second output. The special task without outputs never disappears.
    c = Controller(m.resolve_dependencies(), conn)
    await c.execute(output2)
    assert c.resolve_stale_tasks() == {special}


@pytest.mark.asyncio
async def test_target_not_created(m: Manager, conn: Connection) -> None:
    task = m.create_task("nothing", targets=["missing"])
    c = Controller(m.resolve_dependencies(), conn)
    with pytest.raises(FailedTaskError, match="did not create"):
        await c.execute(task)


@pytest.mark.asyncio
async def test_failing_task(m: Manager, conn: Connection) -> None:
    def raise_exception(_) -> None:
        raise RuntimeError

    task = m.create_task("nothing", action=FunctionAction(raise_exception))
    c = Controller(m.resolve_dependencies(), conn)
    with pytest.raises(FailedTaskError):
        await c.execute(task)
    (last_failed,) = conn.execute(
        "SELECT last_failed FROM tasks WHERE name = 'nothing'"
    ).fetchone()
    assert (datetime.now() - last_failed).total_seconds() < 1


@pytest.mark.asyncio
async def test_concurrency(m: Manager, conn: Connection) -> None:
    delay = 0.2
    num_tasks = 4

    tasks = [
        m.create_task(
            str(i),
            action=SubprocessAction(f"sleep {delay} && touch {i}.txt", shell=True),
            targets=[f"{i}.txt"],
        )
        for i in range(num_tasks)
    ]
    task = m.create_task("result", dependencies=[task.targets[0] for task in tasks])

    c = Controller(m.resolve_dependencies(), conn)
    with Timer() as timer:
        await c.execute(task)
    assert timer.duration > num_tasks * delay

    c = Controller(m.resolve_dependencies(), conn)
    with Timer() as timer:
        await c.execute(task, num_concurrent=num_tasks)
    assert timer.duration < 2 * delay


def test_digest_cache(m: Manager, conn: Connection, tmp_wd: Path) -> None:
    c = Controller(m.resolve_dependencies(), conn)
    shutil.copy(__file__, tmp_wd / "foo")
    with patch("cook.util.evaluate_digest", return_value=b"aaaa") as evaluate_digest:
        c._evaluate_path_hexdigest("foo")
        c._evaluate_path_hexdigest("foo")
    evaluate_digest.assert_called_once()


@pytest.mark.asyncio
async def test_skip_if_no_stale_tasks(
    m: Manager, conn: Connection, tmp_wd: Path
) -> None:
    c = Controller(m.resolve_dependencies(), conn)
    await c.execute([])


@pytest.mark.asyncio
async def test_tasks_are_executed(m: Manager, conn: Connection, tmp_wd: Path) -> None:
    with normalize_dependencies():
        m.create_task("base", targets=["base.txt"], action=FunctionAction(touch))
        task1 = m.create_task(
            "task1",
            targets=["task1.txt"],
            action=FunctionAction(touch),
            dependencies=["base.txt"],
        )
        task2 = m.create_task(
            "task2",
            targets=["task2.txt"],
            action=FunctionAction(touch),
            dependencies=["base.txt"],
        )
    # Execute the first task.
    c = Controller(m.resolve_dependencies(), conn)
    await c.execute(task1)

    # Verify the second is still stale.
    c = Controller(m.resolve_dependencies(), conn)
    assert c.is_stale(task2)

    with open("task2.txt", "w"):
        pass

    c = Controller(m.resolve_dependencies(), conn)
    assert c.is_stale(task2)


def test_is_stale_called_once(m: Manager, conn: Connection) -> None:
    with normalize_dependencies():
        m.create_task("base", targets=["base.txt"], action=FunctionAction(touch))
        m.create_task(
            "task1",
            targets=["task1.txt"],
            action=FunctionAction(touch),
            dependencies=["base.txt"],
        )
        m.create_task(
            "task2",
            targets=["task2.txt"],
            action=FunctionAction(touch),
            dependencies=["base.txt"],
        )

    with patch(
        "cook.controller.Controller._is_self_stale", return_value=False
    ) as _is_self_stale:
        c = Controller(m.resolve_dependencies(), conn)
        [c.is_stale(list(c.dependencies)) for _ in range(7)]

    assert _is_self_stale.call_count == 3


@pytest.mark.asyncio
async def test_stop_long_running_subprocess(m: Manager, conn: Connection) -> None:
    task = m.create_task("sleep", action=SubprocessAction(["sleep", "60"]))
    c = Controller(m.resolve_dependencies(), conn)

    async def cancel_after_delay(task_obj, delay):
        await asyncio.sleep(delay)
        task_obj.cancel()

    with Timer() as timer:
        exec_task = asyncio.create_task(c.execute(task))
        cancel_task = asyncio.create_task(cancel_after_delay(exec_task, 1))

        with pytest.raises(asyncio.CancelledError):
            await exec_task

        await cancel_task

    assert 1 < timer.duration and timer.duration < 2


@pytest.mark.asyncio
async def test_set_stop_between_tasks(m: Manager, conn: Connection) -> None:
    calls = []

    async def _action(task):
        calls.append(task)
        await asyncio.sleep(0.5)

    task1 = m.create_task("sleep1", action=FunctionAction(_action))
    task2 = m.create_task("sleep2", action=FunctionAction(_action))
    c = Controller(m.resolve_dependencies(), conn)

    async def cancel_after_delay(task_obj, delay):
        await asyncio.sleep(delay)
        task_obj.cancel()

    with Timer() as timer:
        exec_task = asyncio.create_task(c.execute([task1, task2]))
        cancel_task = asyncio.create_task(cancel_after_delay(exec_task, 0.3))

        with pytest.raises(asyncio.CancelledError):
            await exec_task

        await cancel_task

    assert 0.3 < timer.duration and timer.duration < 1
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_no_start_after_failure(m: Manager, conn: Connection) -> None:
    calls = []

    async def _action(task):
        calls.append(task)
        # Add a small delay so tasks don't all fail immediately
        await asyncio.sleep(0.01)
        raise ValueError

    # Make task2 depend on task1 so they don't run concurrently
    with normalize_dependencies():
        task1 = m.create_task(
            "sleep1", action=FunctionAction(_action), targets=["t1.txt"]
        )
        task2 = m.create_task(
            "sleep2", action=FunctionAction(_action), dependencies=["t1.txt"]
        )

    c = Controller(m.resolve_dependencies(), conn)

    with pytest.raises(FailedTaskError):
        await c.execute([task1, task2])

    # Only task1 should have been called since it failed and task2 depends on it
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_digest_race(m: Manager, conn: Connection) -> None:
    with normalize_dependencies(), normalize_action():
        task1 = m.create_task("task1", action="echo foo > bar.txt", targets=["bar.txt"])
        task2 = m.create_task(
            "task2",
            action="sleep 1 && echo hello > world.txt",
            targets=["world.txt"],
            dependencies=["bar.txt"],
        )

    # Execute and ...
    c = Controller(m.resolve_dependencies(), conn)
    assert c.is_stale(task2)
    await c.execute(task2)

    # ... ensure the task is no longer stale.
    c = Controller(m.resolve_dependencies(), conn)
    assert not c.is_stale(task2)

    # Modify the file and check the task is stale.
    c = Controller(m.resolve_dependencies(), conn)
    task1.targets[0].write_text("buzz")
    assert c.is_stale(task2)

    # Execute again but modify the dependency during execution.
    c = Controller(m.resolve_dependencies(), conn)

    async def modify_file():
        await asyncio.sleep(0.5)
        task1.targets[0].write_text("fizz")

    modify_task = asyncio.create_task(modify_file())
    await c.execute(task2)
    await modify_task

    c = Controller(m.resolve_dependencies(), conn)
    assert c.is_stale(task2)


@pytest.mark.parametrize(
    "action1, action2",
    [
        (
            SubprocessAction("echo hello > b.txt", shell=True),
            SubprocessAction("echo fizz > b.txt", shell=True),
        ),
        (
            CompositeAction(
                SubprocessAction("echo a > b.txt", shell=True), SubprocessAction("true")
            ),
            CompositeAction(
                SubprocessAction("echo a > b.txt", shell=True),
                SubprocessAction("false"),
            ),
        ),
    ],
)
@pytest.mark.asyncio
async def test_action_digest(
    m: Manager, conn: Connection, action1: Action, action2: Action
) -> None:
    with normalize_dependencies():
        task = m.create_task("task", action=action1, targets=["b.txt"])

    # Execute and check stale status.
    await Controller(m.resolve_dependencies(), conn).execute(task)
    assert not Controller(m.resolve_dependencies(), conn).is_stale(task)

    # Modify the task and check stale status.
    task.action = action2
    assert Controller(m.resolve_dependencies(), conn).is_stale(task)


@pytest.mark.asyncio
async def test_last_started_completed(m: Manager, conn: Connection) -> None:
    with normalize_action():
        task = m.create_task("task", action="sleep 1")
    await Controller(m.resolve_dependencies(), conn).execute(task)
    ((last_started, last_completed),) = conn.execute(
        "SELECT last_started, last_completed FROM tasks"
    ).fetchall()
    delta = last_completed - last_started
    assert delta.total_seconds() > 1


@pytest.mark.asyncio
async def test_last_started_reflects_actual_start(m: Manager, conn: Connection) -> None:
    delay = 0.5
    task1 = m.create_task(
        "task1",
        action=SubprocessAction(f"sleep {delay} && touch task1.txt", shell=True),
        targets=["task1.txt"],
    )
    task2 = m.create_task(
        "task2",
        action=SubprocessAction("touch task2.txt", shell=True),
        targets=["task2.txt"],
    )
    result = m.create_task("result", dependencies=[task1.targets[0], task2.targets[0]])

    # With num_concurrent=1, task2 must wait for task1 to finish. Its last_started
    # should reflect when it actually began executing, not when it was scheduled.
    await Controller(m.resolve_dependencies(), conn).execute(result, num_concurrent=1)
    rows = dict(
        conn.execute(
            "SELECT name, last_started FROM tasks WHERE name IN ('task1', 'task2')"
        ).fetchall()
    )
    delta = (rows["task2"] - rows["task1"]).total_seconds()
    assert delta >= delay, (
        f"task2 started only {delta:.3f}s after task1, expected >= {delay}s; "
        "last_started is recorded at scheduling time, not actual execution time"
    )


@pytest.mark.asyncio
async def test_sync_action_backwards_compat(
    m: Manager, conn: Connection, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that sync execute() methods work with deprecation warning."""

    class SyncAction(Action):
        def __init__(self):
            self.executed = False

        def execute(self, task: Task) -> None:  # type: ignore[override]
            """Old-style sync execute method."""
            self.executed = True

    action = SyncAction()
    task = m.create_task("sync_task", action=action)

    c = Controller(m.resolve_dependencies(), conn)

    # Should emit a warning about sync execute
    await c.execute(task)

    # But should still execute successfully
    assert action.executed

    # Check that warning was logged
    assert "implements sync execute()" in caplog.text


# TODO: add tests to verify what happens when tasks are cancelled, e.g., by `KeyboardInterrupt`.
