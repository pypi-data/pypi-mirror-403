from __future__ import annotations

import os
import platform
from collections.abc import Collection, Generator
from contextlib import ExitStack, contextmanager
from io import TextIOBase
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from typing import Final, TextIO, final

from _atoti_core import (
    LICENSE_KEY_ENV_VAR_NAME,
    OS_WISE_UNIQUE_ID,
    LicenseKeyLocation,
    get_atoti_home,
    java_option,
)

from ._add_opens import ADD_OPENS
from ._copy_output import copy_output
from ._get_java_executable_path import get_java_executable_path
from ._resources_directory import RESOURCES_DIRECTORY
from ._supported_java_version import SUPPORTED_JAVA_VERSION
from .resolve_license_key import resolve_license_key
from .retrieve_spring_application_port import retrieve_spring_application_port

_SERVER_JAR_PATH = RESOURCES_DIRECTORY / "server.jar"

_HADOOP_DIRECTORY = RESOURCES_DIRECTORY / "hadoop-3.2.1"

# Keep in sync with Java's ArgumentParser.BIND_ADDRESS_ARGUMENT
_BIND_ADDRESS_ARGUMENT = "--bind-address"
# Keep in sync with Java's ArgumentParser.ENABLE_AUTH_OPTION.
_ENABLE_AUTH_OPTION = "--enable-auth"
# Keep in sync with Java's ArgumentParser.SESSION_CONFIG_PATH_ARGUMENT.
_SESSION_CONFIG_PATH_ARGUMENT = "--session-config-path"
# Keep in sync with Java's ArgumentParser.PORT_PATH_ARGUMENT.
_PORT_PATH_ARGUMENT = "--port-path"


def _get_logs_directory(session_directory: Path, /) -> Path:
    return session_directory / "logs"


def _create_session_directory() -> Path:
    session_directory = get_atoti_home() / next(OS_WISE_UNIQUE_ID)
    _get_logs_directory(session_directory).mkdir(parents=True)
    return session_directory


def _get_command(
    *,
    address: str | None,
    enable_py4j_auth: bool,
    extra_jars: Collection[Path],
    java_executable_path: Path,
    java_options: Collection[str],
    log_to_stdout: bool,
    port: int,
    py4j_server_port: int | None,
    session_directory: Path,
    session_config_path: Path,
    port_path: Path,
) -> list[Path | str]:
    extra_jars = [
        *[
            jar_path
            for jar_path in RESOURCES_DIRECTORY.glob("*.jar")
            if jar_path != _SERVER_JAR_PATH
        ],
        *extra_jars,
    ]

    command: list[Path | str] = [
        java_executable_path,
        "-jar",
        *ADD_OPENS,
        *[
            java_option(key, value)
            for key, value in {
                "activeviam.feature.experimental.allow_change_measure_type.enabled": "true",
                # Remove following line in 0.9.0.
                "activeviam.feature.experimental.copper_in_distributed_cube.enabled": "true",
                "activeviam.feature.experimental.experimental_copper.enabled": "true",
                "loader.path": ",".join([str(jar_path) for jar_path in extra_jars]),
                "server.port": str(port),
                "server.session_directory": str(session_directory),
            }.items()
        ],
    ]

    if not log_to_stdout:
        command.append(java_option("server.logging.disable_console_logging", "true"))

    if platform.system() == "Windows":
        command.append(java_option("hadoop.home.dir", str(_HADOOP_DIRECTORY)))
        hadoop_path = str(_HADOOP_DIRECTORY / "bin")
        if hadoop_path not in os.environ["PATH"]:
            os.environ["PATH"] = f"{os.environ['PATH']};{hadoop_path}"

    if py4j_server_port is not None:  # pragma: no cover (missing tests)
        command.append(java_option("py4j.port", str(py4j_server_port)))

    command.extend(java_options)

    command.append(_SERVER_JAR_PATH)

    if address is not None:  # pragma: no branch (missing tests)
        command.append(f"{_BIND_ADDRESS_ARGUMENT}={address}")

    if enable_py4j_auth:  # pragma: no branch (missing tests)
        command.append(_ENABLE_AUTH_OPTION)

    command.append(f"{_SESSION_CONFIG_PATH_ARGUMENT}={session_config_path}")

    command.append(f"{_PORT_PATH_ARGUMENT}={port_path}")

    return command


@final
class ServerSubprocess:
    @contextmanager
    @staticmethod
    def create(
        *,
        address: str | None = None,
        enable_py4j_auth: bool = True,
        extra_jars: Collection[Path] = (),
        java_options: Collection[str] = (),
        license_key: LicenseKeyLocation | str,
        logs_destination: Path | TextIO | TextIOBase | None = None,
        session_config_path: Path,
        port_path: Path,
        port: int = 0,
        py4j_server_port: int | None = None,
    ) -> Generator[ServerSubprocess, None, None]:
        java_executable_path = get_java_executable_path(
            supported_java_version=SUPPORTED_JAVA_VERSION,
        )

        session_directory = _create_session_directory()

        match logs_destination:
            case Path():
                logs_path: Path | None = logs_destination
            case TextIO() | TextIOBase():
                logs_path = None
            case None:  # pragma: no branch (avoid `case _` to detect new variants)
                logs_path = _get_logs_directory(session_directory) / "server.log"

        command = _get_command(
            address=address,
            enable_py4j_auth=enable_py4j_auth,
            extra_jars=extra_jars,
            java_executable_path=java_executable_path,
            java_options=java_options,
            log_to_stdout=isinstance(logs_destination, TextIOBase),
            port=port,
            py4j_server_port=py4j_server_port,
            session_directory=session_directory,
            session_config_path=session_config_path,
            port_path=port_path,
        )
        env = (
            None
            if (resolved_license_key := resolve_license_key(license_key)) is None
            else {**os.environ, LICENSE_KEY_ENV_VAR_NAME: resolved_license_key}
        )

        with (
            Popen(  # noqa: S603
                command,
                env=env,
                stderr=STDOUT,
                stdout=PIPE,
                text=True,
            ) as process,
            ExitStack() as exit_stack,
        ):
            exit_stack.callback(process.terminate)

            port, startup_output = retrieve_spring_application_port(port_path, process)

            if isinstance(logs_destination, TextIOBase):
                logs_destination.write(startup_output)
            else:
                startup_log_path = (
                    _get_logs_directory(session_directory) / "startup.log"
                )
                startup_log_path.write_text(startup_output, encoding="utf8")

            if process.stdout is not None:  # pragma: no branch (missing tests)
                output_stream = (
                    logs_destination
                    if isinstance(logs_destination, TextIO | TextIOBase)
                    else None
                )
                exit_stack.enter_context(
                    copy_output(process.stdout, output_stream, close_input_on_exit=True)
                )

            server_subprocess = ServerSubprocess(
                logs_path=logs_path, process=process, port=port
            )
            yield server_subprocess

    def __init__(
        self, *, logs_path: Path | None, process: Popen[str], port: int
    ) -> None:
        self._logs_path: Final = logs_path
        self._process = process
        self.port: Final = port

    @property
    def logs_path(self) -> Path:
        if not self._logs_path:
            raise RuntimeError("Logs are not being written to a file.")

        return self._logs_path

    @property
    def pid(self) -> int:
        return self._process.pid

    def wait(self) -> None:  # pragma: no cover (missing tests)
        """Wait for the process to terminate.

        This will prevent the Python process from exiting.
        If the Py4J gateway is closed the Atoti server will stop itself anyway.
        """
        self._process.wait()
