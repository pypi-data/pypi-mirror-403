import asyncio
import os
from typing import Sequence

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


class ExperimentManager:
    """Async version of ExperimentManager using zmq.asyncio for non-blocking operations."""

    def __init__(self, experiment_id: str, num_workers: int, verbose: bool = False):
        self.context = zmq.asyncio.Context()
        self.experiment_id = experiment_id
        self.num_workers = num_workers
        self.verbose = verbose
        self.connected_workers: dict[str, ServiceState.ValueType] = {}

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

    async def start(self):
        """Start the async state tracking task."""
        if self._state_task is None or self._state_task.done():
            self._state_task = asyncio.create_task(self.state_tracking_loop())

    async def cleanup(self):
        """Clean up resources and stop the manager."""
        self.running = False

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
        """Async loop for tracking worker state updates."""
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
            if client_id in self.connected_workers:
                current_state = self.connected_workers[client_id]
                if self._is_invalid_transition(current_state, message.state):
                    raise ValueError(
                        f"Worker {client_id} has invalid state transition "
                        f"from {self.connected_workers[client_id]} to {message.state}"
                    )

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

    @staticmethod
    def _is_invalid_transition(
        current_state: ServiceState.ValueType, new_state: ServiceState.ValueType
    ) -> bool:
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
