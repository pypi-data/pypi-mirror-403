#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Juha Heljoranta <juha.heljoranta@iki.fi>
# SPDX-License-Identifier: Apache-2.0
import argparse
import logging
import os
import signal
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from types import FrameType

# Try importing dbus, fail gracefully if missing
try:
    import dbus  # type: ignore [import-not-found]
except ImportError:
    sys.stderr.write("Error: 'dbus-python' module is required.\n")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("inhibit")

try:
    __version__ = version("inhibit")
except PackageNotFoundError:
    __version__ = "unknown"


class SleepInhibitor:
    def __init__(self, what: str, who: str, why: str) -> None:
        self.what = what
        self.who = who
        self.why = why
        self.fd: int | None = None
        self.manager: Any = None

        try:
            bus = dbus.SystemBus()
            obj = bus.get_object(
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
            )
            self.manager = dbus.Interface(obj, "org.freedesktop.login1.Manager")
            if self.manager is None:
                logger.critical("Cannot acquire inhibitor: manager is not initialized")
                sys.exit(1)
        except dbus.exceptions.DBusException as e:
            logger.critical(f"Failed to connect to logind: {e}")
            sys.exit(1)

    def acquire(self) -> None:
        if self.fd is not None:
            return

        try:
            fd_wrapper = self.manager.Inhibit(self.what, self.who, self.why, "block")
            self.fd = fd_wrapper.take()
            logger.debug(f"Inhibitor ACQUIRED for '{self.what}' (fd={self.fd})")
        except dbus.exceptions.DBusException:
            logger.exception("Failed to acquire inhibitor via D-Bus")

    def release(self) -> None:
        if self.fd is None:
            return

        fd_to_close = self.fd
        self.fd = None

        try:
            os.close(fd_to_close)
            logger.debug("Inhibitor RELEASED")
        except OSError:
            logger.exception(f"Error closing FD {fd_to_close}")


def setup_input_buffering() -> None:
    """Force stdin to be line-buffered to handle pipe inputs immediately."""
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(line_buffering=True)
    else:
        msg = "Cannot configure line-buffering"
        raise OSError(msg)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Systemd Inhibitor: Reads ON/OFF from stdin to toggle lock.",
    )
    p.add_argument("--strict", action="store_true", help="Exit on malformed input")
    p.add_argument(
        "--what",
        default="sleep",
        choices=[
            "shutdown",
            "sleep",
            "idle",
            "handle-power-key",
            "handle-suspend-key",
            "handle-hibernate-key",
            "handle-lid-switch",
        ],
        help="Target: what operation to block (default: sleep)",
    )
    p.add_argument("--who", default="stdin-inhibitor", help="Identifier string")
    p.add_argument("--why", default="External pipeline request", help="Reason string")
    p.add_argument("--verbose", action="store_true", help="Enable debug logging")
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Print version and exit",
    )
    return p.parse_args()


def _read_stdin(inhibitor: SleepInhibitor, args: argparse.Namespace) -> None:
    for line in sys.stdin:
        command = line.strip().upper()

        if not command:
            continue

        if command == "ON":
            inhibitor.acquire()
        elif command == "OFF":
            inhibitor.release()
        else:
            msg = f"Unknown command: {command!r}"
            if args.strict:
                logger.error(msg)
                sys.exit(1)
            else:
                logger.warning(msg)


def main() -> None:
    args: argparse.Namespace = parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    setup_input_buffering()

    inhibitor = SleepInhibitor(what=args.what, who=args.who, why=args.why)

    def exit_handler(signum: int, _frame: FrameType | None) -> NoReturn:
        sig_name = signal.Signals(signum).name
        logger.debug(f"Received signal {sig_name}, exiting...")
        sys.exit(0)

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    logger.debug("Ready. Waiting for input (ON/OFF)...")

    try:
        _read_stdin(inhibitor, args)
    except BrokenPipeError:
        logger.debug("Input pipe closed (BrokenPipe).")
    except KeyboardInterrupt:
        logger.debug("Interrupted by user.")
    except Exception:
        logger.exception("Unexpected error in main loop")
    finally:
        inhibitor.release()


if __name__ == "__main__":
    main()
