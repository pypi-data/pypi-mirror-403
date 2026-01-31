import os
import threading
from typing import Sequence

import zmq
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
    def __init__(self, experiment_id: str, num_workers: int, verbose: bool = False):
        self.context = zmq.Context()
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
        self._thread = threading.Thread(target=self.state_tracking_thread, daemon=True)
        self._thread.start()

        self.state_cond = threading.Condition()

    def cleanup(self):
        self.running = False
        self._thread.join()

        self.state_socket.close()
        self.command_socket.close()

        self.context.term()

        if os.path.exists(self.state_socket_path):
            os.remove(self.state_socket_path)
        if os.path.exists(self.command_socket_path):
            os.remove(self.command_socket_path)

    def state_tracking_thread(self):
        while self.running:
            try:
                raw_client_id, _, raw_content = self.state_socket.recv_multipart()
            except zmq.error.Again:
                continue

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

            self.state_cond.acquire()
            self.connected_workers[client_id] = message.state
            self.state_cond.notify_all()
            self.state_cond.release()

    def wait_for_all_workers(self, timeout: int | None = None):
        self.state_cond.acquire()
        self.state_cond.wait_for(
            lambda: len(self.connected_workers) == self.num_workers, timeout
        )
        self.state_cond.release()

    def wait_for_workers(self, worker_ids: Sequence[str], timeout: int | None = None):
        self.state_cond.acquire()
        logger.info(self.connected_workers)
        logger.info(self.num_workers)
        self.state_cond.wait_for(
            lambda: all(
                worker_id in self.connected_workers for worker_id in worker_ids
            ),
            timeout,
        )
        self.state_cond.release()

    def wait_for_worker(self, worker_id: str, timeout: int | None = None):
        self.wait_for_workers([worker_id], timeout)

    def wait_for_end_of_all_workers(self, timeout: int | None = None):
        self.state_cond.acquire()
        self.state_cond.wait_for(
            lambda: all(
                state in (ServiceState.DONE, ServiceState.ERROR)
                for state in self.connected_workers.values()
            )
            and len(self.connected_workers) == self.num_workers,
            timeout,
        )
        self.state_cond.release()

    def wait_for_end_of_workers(
        self, worker_ids: Sequence[str], timeout: int | None = None
    ):
        self.state_cond.acquire()
        self.state_cond.wait_for(
            lambda: all(
                worker_id in self.connected_workers
                and self.connected_workers[worker_id]
                in (ServiceState.DONE, ServiceState.ERROR)
                for worker_id in worker_ids
            ),
            timeout,
        )
        self.state_cond.release()

    def wait_for_end_of_worker(self, worker_id: str, timeout: int | None = None):
        self.wait_for_end_of_workers([worker_id], timeout)

    def _send(self, client_id: str, message: Message):
        if self.verbose:
            msg_str = text_format.MessageToString(message, as_one_line=True)
            logger.info(
                f"[evalsync-manager] [+] send message to {client_id}: {msg_str}"
            )
        self.command_socket.send_multipart(
            [client_id.encode(), b"", message.SerializeToString()]
        )

    def _broadcast(self, message: Message):
        for client_id in self.connected_workers:
            self._send(client_id, message)

    def start_all(self):
        self._broadcast(ManagerMessage(command=ExperimentCommand.BEGIN))

    def start_worker(self, worker_id: str):
        if worker_id not in self.connected_workers:
            raise ValueError(f"Worker {worker_id} is not connected to the manager")
        if self.connected_workers[worker_id] not in (
            ServiceState.INIT,
            ServiceState.READY,
        ):
            raise ValueError(f"Worker {worker_id} has already started")
        self._send(
            worker_id,
            ManagerMessage(command=ExperimentCommand.BEGIN),
        )

    def start_workers(self, worker_ids: Sequence[str]):
        for worker_id in worker_ids:
            self.start_worker(worker_id)

    def stop_all(self):
        self._broadcast(ManagerMessage(command=ExperimentCommand.END))

    def stop_worker(self, worker_id: str):
        if worker_id not in self.connected_workers:
            raise ValueError(f"Worker {worker_id} is not connected to the manager")
        if self.connected_workers[worker_id] in (
            ServiceState.INIT,
            ServiceState.READY,
        ):
            raise ValueError(f"Worker {worker_id} has not started")
        self._send(worker_id, ManagerMessage(command=ExperimentCommand.END))

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

    def stop_workers(self, worker_ids: Sequence[str]):
        for worker_id in worker_ids:
            self.stop_worker(worker_id)
