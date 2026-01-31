import os
from typing import Any

import zmq
from google.protobuf import text_format
from loguru import logger

from evalsync.proto.sync_pb2 import (
    ExperimentCommand,
    ManagerMessage,
    ServiceState,
    StateSync,
)


class ExperimentWorker:
    def __init__(
        self, experiment_id: str | None, client_id: str | None, verbose: bool = False
    ):
        self.context = zmq.Context()
        self.experiment_id = (
            experiment_id if experiment_id else os.environ["EVALSYNC_EXPERIMENT_ID"]
        )
        self.client_id = client_id if client_id else os.environ["EVALSYNC_CLIENT_ID"]
        self.state = ServiceState.INIT
        # Check EVALSYNC_VERBOSE environment variable if verbose not explicitly set
        if not verbose and os.environ.get("EVALSYNC_VERBOSE") == "1":
            verbose = True
        self.verbose = verbose

        self.state_socket_path = f"ipc:///tmp/{experiment_id}-STATE"
        self.state_socket = self.context.socket(zmq.DEALER)
        self.state_socket.setsockopt(zmq.LINGER, 1000)
        self.state_socket.setsockopt(zmq.IDENTITY, f"{client_id}".encode())
        self.state_socket.connect(self.state_socket_path)

        if self.verbose:
            logger.info(f"[evalsync-worker] state channel: {self.state_socket_path}")

        self.command_socket_path = f"ipc:///tmp/{experiment_id}-COMMAND"
        self.command_socket = self.context.socket(zmq.DEALER)
        self.command_socket.setsockopt(zmq.LINGER, 1000)
        self.command_socket.setsockopt(zmq.IDENTITY, f"{client_id}".encode())
        self.command_socket.connect(self.command_socket_path)

        if self.verbose:
            logger.info(
                f"[evalsync-worker] command channel: {self.command_socket_path}"
            )

        self.metadata: dict[str, Any] = {}
        self.measurement_started = False
        self.measurement_completed = False

    def cleanup(self):
        self.state_socket.close()
        self.command_socket.close()
        self.context.term()

    def notify_manager(self, msg: str) -> bool:
        message = StateSync(state=self.state, error_message=msg, metadata=self.metadata)

        if self.verbose:
            logger.info(
                f"[evalsync-worker] [+] send message: {text_format.MessageToString(message, as_one_line=True)}"
            )

        self.state_socket.send_multipart([b"", message.SerializeToString()])

        return True

    def ready(self) -> bool:
        if self.verbose:
            logger.info(
                f"[evalsync-worker] API CALL: ready() - current state: {self.state}"
            )
        if self.state == ServiceState.INIT:
            self.state = ServiceState.READY
            self.notify_manager("ready")
            if self.verbose:
                logger.info(
                    "[evalsync-worker] API CALL: ready() - SUCCESS, transitioned to READY"
                )
            return True
        else:
            if self.verbose:
                logger.warning(
                    "[evalsync-worker] API CALL: ready() - FAILED, not in INIT state"
                )
            return False

    def wait_for_start(self) -> bool:
        if self.verbose:
            logger.info(
                f"[evalsync-worker] API CALL: wait_for_start() - current state: {self.state}"
            )
        if self.state == ServiceState.READY:
            while self.state != ServiceState.RUNNING:
                _, raw_message = self.command_socket.recv_multipart()
                message = ManagerMessage()

                ManagerMessage.ParseFromString(message, raw_message)

                if self.verbose:
                    msg_str = text_format.MessageToString(message, as_one_line=True)
                    logger.info(f"[evalsync-worker] [-] receive message: {msg_str}")

                match message.command:
                    case ExperimentCommand.BEGIN:
                        self.state = ServiceState.RUNNING
                        self.notify_manager("running")
                        if self.verbose:
                            logger.info(
                                "[evalsync-worker] API CALL: wait_for_start() - SUCCESS, received BEGIN"
                            )
                        return True
                    case ExperimentCommand.END | ExperimentCommand.ABORT:
                        self.state = ServiceState.ERROR
                        self.notify_manager("error")
                        if self.verbose:
                            logger.warning(
                                "[evalsync-worker] API CALL: wait_for_start() - FAILED, received END/ABORT"
                            )
                        return False
        else:
            if self.verbose:
                logger.warning(
                    "[evalsync-worker] API CALL: wait_for_start() - FAILED, not in READY state"
                )

        return False

    def measure_start(self) -> bool:
        if self.verbose:
            logger.info(
                f"[evalsync-worker] API CALL: measure_start() - current state: {self.state}"
            )
        if self.state == ServiceState.READY:
            self.state = ServiceState.RUNNING
            self.notify_manager("running")
            if self.verbose:
                logger.info(
                    "[evalsync-worker] API CALL: measure_start() - auto-transitioned to RUNNING"
                )
        if self.state == ServiceState.RUNNING:
            self.state = ServiceState.MEASURING
            self.measurement_started = True
            self.measurement_completed = False
            self.notify_manager("measuring")
            if self.verbose:
                logger.info(
                    "[evalsync-worker] API CALL: measure_start() - SUCCESS, transitioned to MEASURING"
                )
            return True
        else:
            if self.verbose:
                logger.warning(
                    "[evalsync-worker] API CALL: measure_start() - FAILED, not in READY or RUNNING state"
                )
            return False

    def measure_end(self) -> bool:
        if self.verbose:
            logger.info(
                f"[evalsync-worker] API CALL: measure_end() - current state: {self.state}"
            )
        if self.state == ServiceState.MEASURING:
            self.state = ServiceState.MEASURE_DONE
            self.measurement_completed = True
            self.notify_manager("measure_done")
            if self.verbose:
                logger.info(
                    "[evalsync-worker] API CALL: measure_end() - SUCCESS, transitioned to MEASURE_DONE"
                )
            return True
        else:
            if self.verbose:
                logger.warning(
                    "[evalsync-worker] API CALL: measure_end() - FAILED, not in MEASURING state"
                )
            return False

    def end(self):
        if self.verbose:
            logger.info(
                f"[evalsync-worker] API CALL: end() - current state: {self.state}"
            )
        if self.state == ServiceState.DONE:
            if self.verbose:
                logger.info(
                    "[evalsync-worker] API CALL: end() - already DONE (no-op)"
                )
            return True
        if self.state == ServiceState.MEASURING:
            # Merge measurement end and workload end into a single transition.
            self.measurement_completed = True
            self.state = ServiceState.DONE
            self.notify_manager("done")
            if self.verbose:
                logger.info(
                    "[evalsync-worker] API CALL: end() - SUCCESS, transitioned to DONE (measurement_end merged)"
                )
            return True
        if self.state == ServiceState.MEASURE_DONE:
            if not self.measurement_completed:
                if self.verbose:
                    logger.warning(
                        "[evalsync-worker] API CALL: end() - FAILED, measurement_end() required before end()"
                    )
                return False
            self.state = ServiceState.DONE
            self.notify_manager("done")
            if self.verbose:
                logger.info(
                    "[evalsync-worker] API CALL: end() - SUCCESS, transitioned to DONE"
                )
            return True
        else:
            if self.verbose:
                logger.warning(
                    "[evalsync-worker] API CALL: end() - FAILED, not in MEASURING or MEASURE_DONE state"
                )
            return False

    def wait_for_stop(self):
        if self.verbose:
            logger.info(
                f"[evalsync-worker] API CALL: wait_for_stop() - current state: {self.state}"
            )
        if self.state in (ServiceState.MEASURING, ServiceState.MEASURE_DONE):
            while self.state != ServiceState.DONE:
                _, raw_message = self.command_socket.recv_multipart()
                message = ManagerMessage()
                ManagerMessage.ParseFromString(message, raw_message)

                if self.verbose:
                    msg_str = text_format.MessageToString(message, as_one_line=True)
                    logger.info(f"[evalsync-worker] [-] received message: {msg_str}")

                match message.command:
                    case ExperimentCommand.END:
                        if self.state == ServiceState.MEASURING:
                            self.measurement_completed = True
                        self.state = ServiceState.DONE
                        self.notify_manager("done")
                        if self.verbose:
                            logger.info(
                                "[evalsync-worker] API CALL: wait_for_stop() - SUCCESS, received END"
                            )
                        return True
                    case ExperimentCommand.BEGIN | ExperimentCommand.ABORT:
                        self.state = ServiceState.ERROR
                        self.notify_manager("error")
                        if self.verbose:
                            logger.warning(
                                "[evalsync-worker] API CALL: wait_for_stop() - FAILED, received BEGIN/ABORT"
                            )
                        return True
        else:
            if self.verbose:
                logger.warning(
                    "[evalsync-worker] API CALL: wait_for_stop() - FAILED, not in MEASURING or MEASURE_DONE state"
                )
        return False
