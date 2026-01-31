import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import zmq
import zmq.asyncio
from google.protobuf import text_format
from google.protobuf.message import Message
from loguru import logger

from evalsync.proto.sync_pb2 import (
    ExperimentCommand,
    ManagerMessage,
    ServiceState,
    StateSync,
)


@dataclass
class StateTransition:
    """Records a state transition with timing information."""

    from_state: ServiceState.ValueType
    to_state: ServiceState.ValueType
    timestamp: float
    metadata: Dict[str, str]


@dataclass
class WorkerTimingInfo:
    """Comprehensive timing information for a worker."""

    worker_id: str
    transitions: List[StateTransition]

    @property
    def init_to_ready_duration(self) -> Optional[float]:
        """Time from INIT to READY state."""
        init_time = self._get_transition_time(ServiceState.INIT)
        ready_time = self._get_transition_time(ServiceState.READY)
        if init_time is not None and ready_time is not None:
            return ready_time - init_time
        return None

    @property
    def ready_to_running_duration(self) -> Optional[float]:
        """Time from READY to RUNNING state (sync wait time)."""
        ready_time = self._get_transition_time(ServiceState.READY)
        running_time = self._get_transition_time(ServiceState.RUNNING)
        if ready_time is not None and running_time is not None:
            return running_time - ready_time
        return None

    @property
    def running_to_done_duration(self) -> Optional[float]:
        """Time from RUNNING to DONE state (execution time)."""
        running_time = self._get_transition_time(ServiceState.RUNNING)
        done_time = self._get_transition_time(ServiceState.DONE)
        if running_time is not None and done_time is not None:
            return done_time - running_time
        return None

    @property
    def measurement_start_time(self) -> Optional[float]:
        """Timestamp when worker entered MEASURING state."""
        return self._get_transition_time(ServiceState.MEASURING)

    @property
    def measurement_end_time(self) -> Optional[float]:
        """Timestamp when worker exited MEASURING (to MEASURE_DONE or DONE)."""
        for transition in self.transitions:
            if transition.from_state == ServiceState.MEASURING and transition.to_state in (
                ServiceState.MEASURE_DONE,
                ServiceState.DONE,
            ):
                return transition.timestamp
        return None

    @property
    def measurement_duration(self) -> Optional[float]:
        """Duration of the measurement phase (MEASURING state).

        This is the most precise timing for benchmarks that use measurement events,
        as it excludes warmup time.
        """
        start = self.measurement_start_time
        end = self.measurement_end_time
        if start is not None and end is not None:
            return end - start
        return None

    @property
    def total_duration(self) -> Optional[float]:
        """Total time from first state to completion."""
        if not self.transitions:
            return None
        first_time = self.transitions[0].timestamp
        last_time = self.transitions[-1].timestamp
        return last_time - first_time

    def _get_transition_time(self, state: ServiceState.ValueType) -> Optional[float]:
        """Get timestamp when worker transitioned to given state."""
        for transition in self.transitions:
            if transition.to_state == state:
                return transition.timestamp
        return None


class ExperimentManager:
    """Async version of ExperimentManager using zmq.asyncio for non-blocking operations with built-in timing."""

    def __init__(
        self,
        experiment_id: str,
        num_workers: int,
        verbose: bool = False,
        enable_timing: bool = True,
    ):
        self.context = zmq.asyncio.Context()
        self.experiment_id = experiment_id
        self.num_workers = num_workers
        self.verbose = verbose
        self.enable_timing = enable_timing
        self.connected_workers: dict[str, ServiceState.ValueType] = {}

        # Built-in timing tracking
        if self.enable_timing:
            self.worker_timings: Dict[str, WorkerTimingInfo] = {}
            self.experiment_start_time: Optional[float] = None
            self.experiment_end_time: Optional[float] = None

        self.state_socket_path = f"ipc:///tmp/{experiment_id}-STATE"
        self.state_socket = self.context.socket(zmq.ROUTER)
        self.state_socket.setsockopt(zmq.LINGER, 1000)
        self.state_socket.setsockopt(zmq.RCVTIMEO, 1000)

        self.state_socket.bind(self.state_socket_path)

        if self.verbose:
            logger.info(f"[evalsync-manager] state channel: {self.state_socket_path}")

        self.command_socket_path = f"ipc:///tmp/{experiment_id}-COMMAND"
        self.command_socket = self.context.socket(zmq.ROUTER)
        self.command_socket.setsockopt(zmq.LINGER, 1000)
        self.command_socket.bind(self.command_socket_path)

        if self.verbose:
            logger.info(
                f"[evalsync-manager] command channel: {self.command_socket_path}"
            )

        self.running = True
        self._state_task: asyncio.Task | None = None

        # Use asyncio.Condition instead of threading.Condition
        self.state_cond = asyncio.Condition()

    @staticmethod
    def _is_invalid_transition(
        current_state: ServiceState.ValueType, new_state: ServiceState.ValueType
    ) -> bool:
        """Check if a state transition is invalid.

        The valid state flow is:

            INIT → READY → RUNNING → MEASURING → MEASURE_DONE → DONE
                                   ↘──────────────→ DONE

        ERROR can be reached from READY, RUNNING, MEASURING, or MEASURE_DONE.
        """
        if current_state == new_state:
            return False
        allowed_next = {
            ServiceState.INIT: {ServiceState.READY},
            ServiceState.READY: {ServiceState.RUNNING, ServiceState.ERROR},
            ServiceState.RUNNING: {ServiceState.MEASURING, ServiceState.ERROR},
            ServiceState.MEASURING: {
                ServiceState.MEASURE_DONE,
                ServiceState.DONE,
                ServiceState.ERROR,
            },
            ServiceState.MEASURE_DONE: {ServiceState.DONE, ServiceState.ERROR},
            ServiceState.DONE: set(),
            ServiceState.ERROR: set(),
        }
        return new_state not in allowed_next.get(current_state, set())

    async def start(self):
        """Start the async state tracking task."""
        if self.enable_timing and self.experiment_start_time is None:
            self.experiment_start_time = time.time()
            if self.verbose:
                logger.info(
                    f"[evalsync-timing] Experiment {self.experiment_id} started at {self.experiment_start_time}"
                )

        if self._state_task is None or self._state_task.done():
            self._state_task = asyncio.create_task(self.state_tracking_loop())

    async def cleanup(self):
        """Clean up resources and stop the manager."""
        self.running = False

        if self.enable_timing and self.experiment_end_time is None:
            self.experiment_end_time = time.time()
            if self.verbose and self.experiment_start_time:
                total_time = self.experiment_end_time - self.experiment_start_time
                logger.info(
                    f"[evalsync-timing] Experiment {self.experiment_id} ended, total duration: {total_time:.3f}s"
                )

        if self._state_task and not self._state_task.done():
            self._state_task.cancel()
            try:
                await self._state_task
            except asyncio.CancelledError:
                pass

        self.state_socket.close()
        self.command_socket.close()

        self.context.term()

        if os.path.exists(self.state_socket_path):
            os.remove(self.state_socket_path)
        if os.path.exists(self.command_socket_path):
            os.remove(self.command_socket_path)

    async def state_tracking_loop(self):
        """Async loop for tracking worker state updates with built-in timing."""
        while self.running:
            try:
                raw_client_id, _, raw_content = await self.state_socket.recv_multipart()
            except zmq.error.Again:
                continue
            except asyncio.CancelledError:
                break

            client_id = raw_client_id.decode()
            message = StateSync()
            StateSync.ParseFromString(message, raw_content)

            # Capture timing information if enabled
            if self.enable_timing:
                current_time = time.time()
                old_state = self.connected_workers.get(client_id, ServiceState.INIT)

                # Initialize worker timing if first time seen
                if client_id not in self.worker_timings:
                    self.worker_timings[client_id] = WorkerTimingInfo(
                        worker_id=client_id, transitions=[]
                    )

                # Record state transition with timing
                transition = StateTransition(
                    from_state=old_state,
                    to_state=message.state,
                    timestamp=current_time,
                    metadata=dict(message.metadata),
                )
                self.worker_timings[client_id].transitions.append(transition)

                # Log timing information for state changes
                if old_state != message.state and self.verbose:
                    state_name = ServiceState.Name(message.state)
                    logger.info(
                        f"[evalsync-timing] Worker {client_id}: {ServiceState.Name(old_state)} -> {state_name} at {current_time:.3f}"
                    )

                    # Log specific timing milestones
                    timing_info = self.worker_timings[client_id]
                    if (
                        message.state == ServiceState.READY
                        and timing_info.init_to_ready_duration
                    ):
                        logger.info(
                            f"[evalsync-timing] Worker {client_id}: initialization took {timing_info.init_to_ready_duration:.3f}s"
                        )
                    elif (
                        message.state == ServiceState.RUNNING
                        and timing_info.ready_to_running_duration
                    ):
                        logger.info(
                            f"[evalsync-timing] Worker {client_id}: sync wait took {timing_info.ready_to_running_duration:.3f}s"
                        )
                    elif (
                        message.state == ServiceState.DONE
                        and timing_info.running_to_done_duration
                    ):
                        logger.info(
                            f"[evalsync-timing] Worker {client_id}: execution took {timing_info.running_to_done_duration:.3f}s"
                        )
                        if timing_info.total_duration:
                            logger.info(
                                f"[evalsync-timing] Worker {client_id}: total duration {timing_info.total_duration:.3f}s"
                            )

            if self.verbose:
                msg_str = text_format.MessageToString(message, as_one_line=True)
                logger.info(
                    f"[evalsync-manager] [-] receive message from {raw_client_id.decode()}: {msg_str}"
                )

            if (
                client_id not in self.connected_workers
                and len(self.connected_workers) >= self.num_workers
            ):
                raise ValueError("Accept more workers than expected")
            elif (
                client_id in self.connected_workers
                and self._is_invalid_transition(self.connected_workers[client_id], message.state)
            ):
                raise ValueError(
                    f"Worker {client_id} has invalid state transition "
                    f"from {self.connected_workers[client_id]} to {message.state}"
                )
            else:
                if client_id not in self.connected_workers:
                    logger.info(f"Worker {client_id} connected")

                async with self.state_cond:
                    self.connected_workers[client_id] = message.state
                    self.state_cond.notify_all()

    async def wait_for_all_workers(self, timeout: float | None = None):
        """Wait for all expected workers to connect."""
        async with self.state_cond:
            try:
                await asyncio.wait_for(
                    self.state_cond.wait_for(
                        lambda: len(self.connected_workers) == self.num_workers
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                pass

    async def wait_for_workers(
        self, worker_ids: Sequence[str], timeout: float | None = None
    ):
        """Wait for specific workers to connect."""
        async with self.state_cond:
            if self.verbose:
                logger.info(f"Connected workers: {self.connected_workers}")
                logger.info(f"Expected workers: {self.num_workers}")
            try:
                await asyncio.wait_for(
                    self.state_cond.wait_for(
                        lambda: all(
                            worker_id in self.connected_workers
                            for worker_id in worker_ids
                        )
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                pass

    async def wait_for_worker(self, worker_id: str, timeout: float | None = None):
        """Wait for a specific worker to connect."""
        await self.wait_for_workers([worker_id], timeout)

    async def wait_for_end_of_all_workers(self, timeout: float | None = None):
        """Wait for all workers to reach DONE or ERROR state."""
        async with self.state_cond:
            try:
                await asyncio.wait_for(
                    self.state_cond.wait_for(
                        lambda: all(
                            state in (ServiceState.DONE, ServiceState.ERROR)
                            for state in self.connected_workers.values()
                        )
                        and len(self.connected_workers) == self.num_workers
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                pass

    async def wait_for_end_of_workers(
        self, worker_ids: Sequence[str], timeout: float | None = None
    ):
        """Wait for specific workers to reach DONE or ERROR state."""
        async with self.state_cond:
            try:
                await asyncio.wait_for(
                    self.state_cond.wait_for(
                        lambda: all(
                            worker_id in self.connected_workers
                            and self.connected_workers[worker_id]
                            in (ServiceState.DONE, ServiceState.ERROR)
                            for worker_id in worker_ids
                        )
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                pass

    async def wait_for_end_of_worker(
        self, worker_id: str, timeout: float | None = None
    ):
        """Wait for a specific worker to reach DONE or ERROR state."""
        await self.wait_for_end_of_workers([worker_id], timeout)

    async def wait_for_all_measuring(self, timeout: float | None = None):
        """Wait for all workers to enter MEASURING state.

        Uses transition history to detect if workers have entered MEASURING,
        so it works even if some workers have already advanced past MEASURING.

        Workers that reach MEASURE_DONE/DONE/ERROR without entering MEASURING
        are treated as having satisfied the condition (they won't block forever).

        Raises:
            RuntimeError: If timing is not enabled for this manager.
        """
        if not self.enable_timing:
            raise RuntimeError(
                "wait_for_all_measuring requires enable_timing=True"
            )

        def _worker_entered_measuring_or_finished(worker_id: str) -> bool:
            timing = self.worker_timings.get(worker_id)
            if timing and timing.measurement_start_time is not None:
                return True
            state = self.connected_workers.get(worker_id, ServiceState.INIT)
            return state in (
                ServiceState.MEASURE_DONE,
                ServiceState.DONE,
                ServiceState.ERROR,
            )

        async with self.state_cond:
            try:
                await asyncio.wait_for(
                    self.state_cond.wait_for(
                        lambda: len(self.connected_workers) == self.num_workers
                        and all(
                            _worker_entered_measuring_or_finished(worker_id)
                            for worker_id in self.connected_workers
                        )
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                pass

    async def wait_for_measuring_done(self, timeout: float | None = None):
        """Wait for any worker to exit MEASURING state (transition to MEASURE_DONE/DONE or ERROR).

        Returns as soon as any worker that was previously MEASURING transitions out,
        or any worker reaches MEASURE_DONE/DONE/ERROR without entering MEASURING.

        Raises:
            RuntimeError: If timing is not enabled for this manager.
        """
        if not self.enable_timing:
            raise RuntimeError(
                "wait_for_measuring_done requires enable_timing=True"
            )

        def _worker_finished_measuring_or_done(worker_id: str) -> bool:
            timing = self.worker_timings.get(worker_id)
            if timing and timing.measurement_end_time is not None:
                return True
            state = self.connected_workers.get(worker_id, ServiceState.INIT)
            return state in (
                ServiceState.MEASURE_DONE,
                ServiceState.DONE,
                ServiceState.ERROR,
            )

        async with self.state_cond:
            try:
                await asyncio.wait_for(
                    self.state_cond.wait_for(
                        lambda: any(
                            _worker_finished_measuring_or_done(worker_id)
                            for worker_id in self.connected_workers
                        )
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                pass

    async def _send(self, client_id: str, message: Message):
        """Send a message to a specific worker."""
        if self.verbose:
            msg_str = text_format.MessageToString(message, as_one_line=True)
            logger.info(
                f"[evalsync-manager] [+] send message to {client_id}: {msg_str}"
            )
        await self.command_socket.send_multipart(
            [client_id.encode(), b"", message.SerializeToString()]
        )

    async def _broadcast(self, message: Message):
        """Broadcast a message to all connected workers."""
        for client_id in self.connected_workers:
            await self._send(client_id, message)

    async def start_all(self):
        """Start all connected workers."""
        await self._broadcast(ManagerMessage(command=ExperimentCommand.BEGIN))

    async def start_worker(self, worker_id: str):
        """Start a specific worker."""
        if worker_id not in self.connected_workers:
            raise ValueError(f"Worker {worker_id} is not connected to the manager")
        if self.connected_workers[worker_id] not in (
            ServiceState.INIT,
            ServiceState.READY,
        ):
            raise ValueError(f"Worker {worker_id} has already started")
        await self._send(
            worker_id,
            ManagerMessage(command=ExperimentCommand.BEGIN),
        )

    async def start_workers(self, worker_ids: Sequence[str]):
        """Start multiple specific workers."""
        for worker_id in worker_ids:
            await self.start_worker(worker_id)

    async def stop_all(self):
        """Stop all connected workers."""
        await self._broadcast(ManagerMessage(command=ExperimentCommand.END))

    async def stop_worker(self, worker_id: str):
        """Stop a specific worker."""
        if worker_id not in self.connected_workers:
            raise ValueError(f"Worker {worker_id} is not connected to the manager")
        if self.connected_workers[worker_id] in (
            ServiceState.INIT,
            ServiceState.READY,
        ):
            raise ValueError(f"Worker {worker_id} has not started")
        await self._send(worker_id, ManagerMessage(command=ExperimentCommand.END))

    async def stop_workers(self, worker_ids: Sequence[str]):
        """Stop multiple specific workers."""
        for worker_id in worker_ids:
            await self.stop_worker(worker_id)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    # Built-in timing query methods
    def get_timing_summary(self) -> Dict[str, Any]:
        """Get comprehensive timing summary for all workers (only available when timing is enabled)."""
        if not self.enable_timing:
            return {"error": "Timing is not enabled for this experiment manager"}

        summary: dict[str, Any] = {
            "experiment_id": self.experiment_id,
            "experiment_start_time": self.experiment_start_time,
            "experiment_end_time": self.experiment_end_time,
            "total_experiment_duration": (self.experiment_end_time or time.time())
            - (self.experiment_start_time or 0),
            "workers": {},
        }

        for worker_id, timing_info in self.worker_timings.items():
            summary["workers"][worker_id] = {
                "init_to_ready_duration": timing_info.init_to_ready_duration,
                "ready_to_running_duration": timing_info.ready_to_running_duration,
                "running_to_done_duration": timing_info.running_to_done_duration,
                "measurement_start_time": timing_info.measurement_start_time,
                "measurement_end_time": timing_info.measurement_end_time,
                "measurement_duration": timing_info.measurement_duration,
                "total_duration": timing_info.total_duration,
                "transitions": [
                    {
                        "from_state": ServiceState.Name(t.from_state),
                        "to_state": ServiceState.Name(t.to_state),
                        "timestamp": t.timestamp,
                        "metadata": t.metadata,
                    }
                    for t in timing_info.transitions
                ],
            }

        return summary

    def get_worker_timing(self, worker_id: str) -> Optional[WorkerTimingInfo]:
        """Get timing information for specific worker (only available when timing is enabled)."""
        if not self.enable_timing:
            return None
        return self.worker_timings.get(worker_id)

    def is_worker_measuring(self, worker_id: str) -> bool:
        """Check if a specific worker is currently in MEASURING state."""
        return self.connected_workers.get(worker_id) == ServiceState.MEASURING

    def any_worker_measuring(self) -> bool:
        """Check if any worker is currently in MEASURING state."""
        return any(state == ServiceState.MEASURING for state in self.connected_workers.values())

    def all_workers_measuring(self) -> bool:
        """Check if all connected workers are in MEASURING state."""
        if not self.connected_workers:
            return False
        return all(state == ServiceState.MEASURING for state in self.connected_workers.values())
