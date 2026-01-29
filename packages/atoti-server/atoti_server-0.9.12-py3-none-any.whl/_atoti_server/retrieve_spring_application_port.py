import time
from contextlib import ExitStack
from datetime import timedelta
from io import StringIO
from pathlib import Path
from subprocess import Popen

from ._copy_output import copy_output


def retrieve_spring_application_port(
    port_path: Path, process: Popen[str] | None
) -> tuple[int, str]:  # pragma: no cover (missing tests)
    """Polls the given file until the Spring application port is written in it.

    Returns the port and a string representing the given process' output.
    In no process is given, the string will be empty.
    """
    with ExitStack() as exit_stack, StringIO() as output:
        if process is not None and process.stdout is not None:
            exit_stack.enter_context(
                copy_output(process.stdout, output, close_input_on_exit=False)
            )

        timeout = timedelta(minutes=2)

        try:
            port = _poll_for_port(port_path, process=process, timeout=timeout)
            return port, output.getvalue()
        except RuntimeError as error:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    process.wait()
                if process.stdout is not None:
                    process.stdout.close()
            raise RuntimeError(
                f"Could not retrieve the port of the Atoti Spring application from {port_path} within {timeout.seconds} seconds: {error}\n"
                f"Server logs:\n{output.getvalue() or '(no output)'}"
            ) from error


def _poll_for_port(
    path: Path, *, process: Popen[str] | None, timeout: timedelta
) -> int:  # pragma: no cover (missing tests)
    start_time = time.monotonic()

    while time.monotonic() < start_time + timeout.total_seconds():
        if process is not None:
            exit_code = process.poll()
            if exit_code is not None:
                raise RuntimeError(f"Process exited with exit code {exit_code}")

        try:
            with path.open() as file:
                port_info = file.readline()
                if port_info.endswith("\n"):
                    return int(port_info.rstrip("\n"))
        except FileNotFoundError:
            pass

        time.sleep(1)

    raise RuntimeError("Timed out")
