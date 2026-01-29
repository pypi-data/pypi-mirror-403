from collections.abc import Generator
from contextlib import contextmanager
from io import TextIOBase
from threading import Event, Thread
from typing import IO, TextIO


@contextmanager
def copy_output(
    input_stream: IO[str],
    output_stream: TextIO | TextIOBase | None,
    *,
    close_input_on_exit: bool,
) -> Generator[None, None, None]:
    should_stop = Event()

    def copy_stream() -> None:
        try:
            for line in input_stream:
                if output_stream and not output_stream.closed:
                    output_stream.write(line)
                if should_stop.is_set():
                    break
        except ValueError:  # pragma: no cover
            pass  # "I/O operation on closed file"

        if close_input_on_exit and not input_stream.closed:
            input_stream.close()

    thread = Thread(target=copy_stream, daemon=True)
    thread.start()

    yield

    should_stop.set()
