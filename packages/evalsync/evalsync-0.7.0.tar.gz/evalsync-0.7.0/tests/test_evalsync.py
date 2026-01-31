import time
import uuid

import pytest
from evalsync import ExperimentManager, ExperimentWorker


@pytest.mark.timeout(15)
def test_normal_flow():
    experiment_id = f"{uuid.uuid4()}"

    manager = ExperimentManager(experiment_id, 1, True)
    worker = ExperimentWorker(experiment_id, "client", True)

    time.sleep(1)

    worker.ready()
    print("worker is ready")

    manager.wait_for_all_workers()
    manager.start_all()
    worker.wait_for_start()
    worker.measure_start()
    worker.measure_end()
    manager.stop_all()
    worker.wait_for_stop()

    worker.cleanup()
    manager.cleanup()


@pytest.mark.timeout(15)
def test_multiple_workers():
    experiment_id = f"{uuid.uuid4()}"

    NUM_WORKERS = 10

    manager = ExperimentManager(experiment_id, NUM_WORKERS, True)
    workers = [ExperimentWorker(experiment_id, f"client-{i}", True) for i in range(NUM_WORKERS)]

    time.sleep(1)

    for worker in workers:
        worker.ready()

    print("worker is ready")

    manager.wait_for_all_workers()
    manager.start_all()

    for worker in workers:
        worker.wait_for_start()
        worker.measure_start()

    for worker in workers:
        worker.measure_end()

    manager.stop_all()

    for worker in workers:
        worker.wait_for_stop()

    for worker in workers:
        worker.cleanup()

    manager.cleanup()


@pytest.mark.timeout(15)
def test_multiple_group_of_workers():
    experiment_id = f"{uuid.uuid4()}"

    NUM_WORKERS = 10
    NUM_GROUP1 = 3

    GROUP1 = [f"client-{i}" for i in range(NUM_GROUP1)]
    GROUP2 = [f"client-{i}" for i in range(NUM_GROUP1, NUM_WORKERS)]

    manager = ExperimentManager(experiment_id, NUM_WORKERS, True)
    workers = [ExperimentWorker(experiment_id, f"client-{i}", True) for i in range(NUM_WORKERS)]

    time.sleep(1)

    for worker in workers[:NUM_GROUP1]:
        worker.ready()

    manager.wait_for_workers(GROUP1)
    manager.start_workers(GROUP1)

    for worker in workers[:NUM_GROUP1]:
        worker.wait_for_start()
        worker.measure_start()

    for worker in workers[:NUM_GROUP1]:
        worker.measure_end()

    manager.stop_workers(GROUP1)
    for worker in workers[:NUM_GROUP1]:
        worker.wait_for_stop()

    for worker in workers[NUM_GROUP1:]:
        worker.ready()

    manager.wait_for_workers(GROUP2)
    manager.start_workers(GROUP2)
    for worker in workers[NUM_GROUP1:]:
        worker.wait_for_start()
        worker.measure_start()

    for worker in workers[NUM_GROUP1:]:
        worker.measure_end()

    manager.stop_workers(GROUP2)
    for worker in workers[NUM_GROUP1:]:
        worker.wait_for_stop()

    for worker in workers:
        worker.cleanup()

    manager.cleanup()
