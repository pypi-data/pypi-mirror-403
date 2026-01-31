import asyncio
import sys
from pathlib import Path
from subprocess import SubprocessError
from unittest import mock

import pytest

from cook.actions import CompositeAction, FunctionAction, ModuleAction, SubprocessAction
from cook.util import Timer


@pytest.mark.asyncio
async def test_shell_action(tmp_wd: Path) -> None:
    action = SubprocessAction("echo hello > world.txt", shell=True)
    await action.execute(None)  # type: ignore[arg-type]
    assert (tmp_wd / "world.txt").read_text().strip() == "hello"


@pytest.mark.asyncio
async def test_shell_action_timeout() -> None:
    action = SubprocessAction(["sleep", "60"])

    async def cancel_after_delay(task_obj, delay):
        await asyncio.sleep(delay)
        task_obj.cancel()

    with Timer() as timer:
        exec_task = asyncio.create_task(action.execute(None))  # type: ignore[arg-type]
        cancel_task = asyncio.create_task(cancel_after_delay(exec_task, 1))

        with pytest.raises(asyncio.CancelledError):
            await exec_task

        await cancel_task

    assert 1 < timer.duration < 2


@pytest.mark.asyncio
async def test_shell_action_kill_on_timeout() -> None:
    """Test that subprocess is killed if it doesn't terminate within timeout."""
    with mock.patch("asyncio.create_subprocess_exec") as create_subprocess:
        # Mock a process that doesn't terminate gracefully
        mock_process = mock.MagicMock()
        mock_process.returncode = None

        # Make wait() timeout on first call, then succeed
        wait_count = 0

        async def mock_wait():
            nonlocal wait_count
            wait_count += 1
            if wait_count == 1:
                # First wait() is the normal execution wait
                raise asyncio.CancelledError()
            elif wait_count == 2:
                # Second wait() inside wait_for() times out
                raise asyncio.TimeoutError()
            else:
                # Third wait() after kill() succeeds
                return 0

        mock_process.wait = mock.AsyncMock(side_effect=mock_wait)
        mock_process.terminate = mock.MagicMock()
        mock_process.kill = mock.MagicMock()
        create_subprocess.return_value = mock_process

        action = SubprocessAction(["sleep", "60"])

        with pytest.raises(asyncio.CancelledError):
            await action.execute(None)  # type: ignore[arg-type]

        # Verify terminate and kill were called
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()


@pytest.mark.asyncio
async def test_subprocess_action(tmp_wd: Path) -> None:
    action = SubprocessAction(["touch", "foo"])
    await action.execute(None)  # type: ignore[arg-type]
    assert (tmp_wd / "foo").is_file()


@pytest.mark.asyncio
async def test_bad_subprocess_action() -> None:
    action = SubprocessAction("false")
    with pytest.raises(SubprocessError):
        await action.execute(None)  # type: ignore[arg-type]


def test_shell_action_with_list_args() -> None:
    """Test that shell=True with list args raises ValueError at construction."""
    with pytest.raises(ValueError, match="shell=True requires string args"):
        SubprocessAction(["echo", "hello"], shell=True)


def test_subprocess_action_repr() -> None:
    assert repr(SubprocessAction("false")) == "SubprocessAction('false')"
    assert repr(SubprocessAction(["wait", "3"])) == "SubprocessAction('wait 3')"


@pytest.mark.asyncio
async def test_function_action() -> None:
    args = []

    action = FunctionAction(args.append)
    await action.execute(42)  # type: ignore[arg-type]

    assert args == [42]


@pytest.mark.asyncio
async def test_composite_action() -> None:
    args = []

    action = CompositeAction(FunctionAction(args.append), FunctionAction(args.append))
    await action.execute("hello")  # type: ignore[arg-type]
    assert args == ["hello", "hello"]


@pytest.mark.asyncio
async def test_module_action() -> None:
    action = ModuleAction([pytest, "-h"])
    await action.execute(None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="shell execution"):
        ModuleAction([pytest], shell=True)

    with pytest.raises(ValueError, match="not be empty"):
        ModuleAction([])

    with pytest.raises(TypeError, match="must be a module"):
        ModuleAction([None])


@pytest.mark.asyncio
async def test_module_action_debug() -> None:
    with mock.patch("asyncio.create_subprocess_exec") as create_subprocess:
        # Mock the process
        mock_process = mock.MagicMock()
        mock_process.wait = mock.AsyncMock(return_value=0)
        create_subprocess.return_value = mock_process

        await ModuleAction([pytest], debug=True).execute(None)  # type: ignore[arg-type]
        create_subprocess.assert_called_with(
            sys.executable, "-m", "pdb", "-m", "pytest"
        )

    with mock.patch("asyncio.create_subprocess_exec") as create_subprocess:
        # Mock the process
        mock_process = mock.MagicMock()
        mock_process.wait = mock.AsyncMock(return_value=0)
        create_subprocess.return_value = mock_process

        await ModuleAction([pytest], debug=False).execute(None)  # type: ignore[arg-type]
        create_subprocess.assert_called_with(sys.executable, "-m", "pytest")


@pytest.mark.asyncio
async def test_sync_function_action_with_kwargs() -> None:
    calls = []

    def func(task, *, key):
        calls.append((task, key))

    action = FunctionAction(func, key="value")
    await action.execute("my_task")  # type: ignore[arg-type]
    assert calls == [("my_task", "value")]


def test_composite_digest() -> None:
    actions = [
        SubprocessAction("hello"),
        SubprocessAction(["foo", "bar"]),
    ]
    assert CompositeAction(*actions).hexdigest

    actions.append(FunctionAction(print))  # type: ignore[arg-type]
    assert CompositeAction(*actions).hexdigest is None
