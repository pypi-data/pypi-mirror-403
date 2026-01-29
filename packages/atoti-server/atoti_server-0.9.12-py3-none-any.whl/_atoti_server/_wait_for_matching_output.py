from __future__ import annotations

import re
from datetime import timedelta
from io import StringIO
from subprocess import Popen, list2cmdline
from time import monotonic

_DEFAULT_TIMEOUT = timedelta(minutes=3)


def wait_for_matching_output(
    pattern: str,
    *,
    process: Popen[str],
    timeout: timedelta = _DEFAULT_TIMEOUT,
) -> tuple[re.Match[str], str]:
    assert process.stdout is not None

    with StringIO() as output:

        def get_error_message(
            *, reason: str
        ) -> str:  # pragma: no cover (missing tests)
            assert isinstance(process.args, list | tuple)
            command = list2cmdline(process.args)
            return "\n".join(
                [
                    reason,
                    "COMMAND:",
                    command,
                    "PATTERN:",
                    pattern,
                    "OUTPUT:",
                    "".join(output.getvalue()),
                ],
            )

        start = monotonic()

        try:
            while process.poll() is None:
                if (
                    monotonic() > start + timeout.total_seconds()
                ):  # pragma: no cover (missing tests)
                    raise RuntimeError(
                        get_error_message(
                            reason=f"{timeout.total_seconds()} seconds elapsed but the process output did not match the expected pattern.",
                        ),
                    )

                line = process.stdout.readline()
                output.write(line)

                match = re.search(pattern, line)
                if match:
                    return match, output.getvalue()

            raise RuntimeError(  # pragma: no cover (missing tests)
                get_error_message(
                    reason="Process exited before its output matched the expected pattern.",
                ),
            )
        except:  # pragma: no cover (missing tests)
            if not process.stdout.closed:
                process.stdout.close()
            raise
