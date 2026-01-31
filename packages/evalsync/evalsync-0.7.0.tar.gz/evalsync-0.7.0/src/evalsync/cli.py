import os
import signal
import subprocess
import sys
import time
from typing import List

import typer
from loguru import logger
import zmq

from evalsync.manager import ExperimentManager
from evalsync.worker import ExperimentWorker

app = typer.Typer()


@app.command()
def demo(
    experiment_id: str = typer.Option(),
    num_workers: int = typer.Option(1),
    duration: int = typer.Option(10),
    verbose: bool = typer.Option(False),
    role: str = typer.Option(
        "server", "--role", help="Role to play: 'server' or 'client'"
    ),
):
    """
    Run evalsync demo - can act as server (manager) or client (worker).

    Server mode: Manages an experiment and coordinates workers.
    Client mode: Connects as a worker and follows the evalsync protocol.
    """
    if role == "server":
        manager = ExperimentManager(experiment_id, num_workers, verbose)
        manager.wait_for_all_workers()
        logger.info("All workers are ready")
        manager.start_all()
        time.sleep(duration)
        manager.stop_all()
        manager.cleanup()
    elif role == "client":
        # Basic evalsync client - just follows the protocol without wrapping commands
        client_id = f"demo-client-{os.getpid()}"
        worker = ExperimentWorker(experiment_id, client_id, verbose)
        worker.ready()
        worker.wait_for_start()
        worker.measure_start()
        # Simulate some work
        if verbose:
            logger.info(f"[demo-client] Simulating work for {duration} seconds")
        time.sleep(duration)
        worker.measure_end()
        worker.wait_for_stop()
        worker.cleanup()
    else:
        logger.error(f"Invalid role: {role}. Must be 'server' or 'client'")
        raise typer.Exit(1)


@app.command()
def wrap(
    command: List[str] = typer.Argument(..., help="Command and arguments to wrap"),
    experiment_id: str | None = typer.Option(
        None,
        "-e",
        "--experiment-id",
        help="Experiment ID (can also use EVALSYNC_EXPERIMENT_ID env var)",
    ),
    client_id: str | None = typer.Option(
        None, "-c", "--client-id", help="Client ID (defaults to evalsync-wrapper-<PID>)"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Enable verbose logging"
    ),
    timeout: int = typer.Option(
        300, "-t", "--timeout", help="Timeout for evalsync operations in seconds"
    ),
):
    """
    Wrap arbitrary CLI programs with evalsync coordination.

    This command automatically provides evalsync functionality for any CLI program:
    1. Sends READY signal to evalsync manager
    2. Waits for START signal from manager
    3. Marks measurement start
    4. Executes the wrapped command
    5. Marks measurement end
    6. Sends DONE signal when command completes
    7. Cleans up evalsync resources

    Examples:
        evalsyncli wrap -e "test-001" -c "client-1" -- whoami
        evalsyncli wrap -e "bench-test" --verbose -- sleep 5
        evalsyncli wrap -e "iperf-test" -- iperf3 -c server -t 30 -P 4
    """
    # Handle environment variables and defaults
    if experiment_id is None:
        experiment_id = os.environ.get("EVALSYNC_EXPERIMENT_ID")
        if experiment_id is None:
            logger.error(
                "Experiment ID is required. Set with -e/--experiment-id or EVALSYNC_EXPERIMENT_ID environment variable"
            )
            raise typer.Exit(1)

    if client_id is None:
        client_id = os.environ.get(
            "EVALSYNC_CLIENT_ID", f"evalsync-wrapper-{os.getpid()}"
        )

    # Check environment variable for verbose if not explicitly set
    if not verbose and os.environ.get("EVALSYNC_VERBOSE", "").lower() in ("true", "1"):
        verbose = True

    if verbose:
        logger.info(f"[evalsync-wrapper] Starting evalsync wrapper")
        logger.info(f"[evalsync-wrapper] Experiment ID: {experiment_id}")
        logger.info(f"[evalsync-wrapper] Client ID: {client_id}")
        logger.info(f"[evalsync-wrapper] Command: {' '.join(command)}")

    # Initialize evalsync worker
    worker = ExperimentWorker(experiment_id, client_id, verbose)

    # Set socket timeout for evalsync operations (timeout in milliseconds)
    timeout_ms = timeout * 1000
    worker.command_socket.setsockopt(zmq.RCVTIMEO, timeout_ms)

    exit_code = 0
    process = None

    def signal_handler(signum, frame):
        if verbose:
            signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
            logger.info(f"[evalsync-wrapper] Received {signal_name}")

        if process and process.poll() is None:
            if verbose:
                logger.info(f"[evalsync-wrapper] Terminating child process {process.pid}")

            try:
                with open(f"/proc/{process.pid}/stat", "r") as f:
                    stat_fields = f.read().split()
                    if len(stat_fields) > 2 and stat_fields[2].startswith("T"):
                        if verbose:
                            logger.info(f"[evalsync-wrapper] Process {process.pid} is suspended, sending SIGCONT first")
                        try:
                            os.kill(process.pid, signal.SIGCONT)
                            time.sleep(0.1)
                        except (ProcessLookupError, OSError):
                            pass
            except (OSError, IndexError):
                pass

            try:
                process.terminate()
                process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if verbose:
                    logger.info("[evalsync-wrapper] Child didn't exit, force killing")
                try:
                    process.kill()
                except ProcessLookupError:
                    pass

        sys.exit(130 if signum == signal.SIGINT else 143)

    # Install signal handlers early
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    measurement_started = False
    try:
        # Phase 1: Send READY signal
        if verbose:
            logger.info("[evalsync-wrapper] Sending READY signal")
        worker.ready()

        # Phase 2: Wait for START signal (with timeout)
        if verbose:
            logger.info(
                f"[evalsync-wrapper] Waiting for START signal (timeout: {timeout}s)"
            )

        try:
            worker.wait_for_start()
        except zmq.Again:
            logger.error(
                f"[evalsync-wrapper] Timeout waiting for START signal after {timeout} seconds"
            )
            raise typer.Exit(1)

        if verbose:
            logger.info("[evalsync-wrapper] Marking measurement start")
        if worker.measure_start():
            measurement_started = True

        # Phase 3: Execute the wrapped command
        if verbose:
            logger.info(f"[evalsync-wrapper] Executing command: {' '.join(command)}")

        # Start child in same process group so SIGSTOP affects both wrapper and child
        if verbose:
            logger.info("[evalsync-wrapper] Starting child in same process group")
        process = subprocess.Popen(command)
        exit_code = process.wait()

        if verbose:
            logger.info(
                f"[evalsync-wrapper] Command completed with exit code: {exit_code}"
            )

    except Exception as e:
        if verbose:
            logger.error(f"[evalsync-wrapper] Error executing command: {e}")
        exit_code = 1
    finally:
        if measurement_started:
            if verbose:
                logger.info("[evalsync-wrapper] Marking measurement end")
            worker.measure_end()

    try:
        # Phase 4: Send DONE signal (wait_for_stop handles this) with timeout
        if verbose:
            logger.info(
                f"[evalsync-wrapper] Waiting for STOP signal (timeout: {timeout}s)"
            )

        try:
            worker.end()
        except zmq.Again:
            logger.warning(
                f"[evalsync-wrapper] Timeout waiting for STOP signal after {timeout} seconds, continuing with cleanup"
            )

        if verbose:
            logger.info("[evalsync-wrapper] Cleaning up evalsync resources")
        worker.cleanup()

    except Exception as e:
        if verbose:
            logger.error(f"[evalsync-wrapper] Error during cleanup: {e}")
        if exit_code == 0:  # Only override exit code if command succeeded
            exit_code = 1

    if verbose:
        logger.info(
            f"[evalsync-wrapper] Wrapper complete, exiting with code: {exit_code}"
        )

    sys.exit(exit_code)


def main():
    app()


if __name__ == "__main__":
    app()
