"""Tests for the async ExperimentManager."""

import asyncio
import pytest

from evalsync.aio.manager import ExperimentManager


@pytest.mark.asyncio
async def test_async_manager_creation():
    """Test that async manager can be created and cleaned up."""
    manager = ExperimentManager("test-experiment", num_workers=2, verbose=True)
    
    # Test async context manager
    async with manager:
        assert manager.experiment_id == "test-experiment"
        assert manager.num_workers == 2
        assert manager.verbose is True
        assert len(manager.connected_workers) == 0


@pytest.mark.asyncio
async def test_async_manager_lifecycle():
    """Test async manager start and cleanup."""
    manager = ExperimentManager("test-lifecycle", num_workers=1, verbose=False)
    
    # Start the manager
    await manager.start()
    assert manager._state_task is not None
    assert not manager._state_task.done()
    
    # Cleanup
    await manager.cleanup()
    assert not manager.running


@pytest.mark.asyncio
async def test_async_manager_timeout_operations():
    """Test timeout operations don't hang indefinitely."""
    manager = ExperimentManager("test-timeout", num_workers=2, verbose=False)
    
    async with manager:
        # These should timeout quickly since no workers are connected
        await manager.wait_for_all_workers(timeout=0.1)
        await manager.wait_for_worker("nonexistent", timeout=0.1)
        await manager.wait_for_end_of_all_workers(timeout=0.1)


if __name__ == "__main__":
    # Simple test runner for development
    async def run_tests():
        print("Testing async manager creation...")
        await test_async_manager_creation()
        print("✓ Async manager creation test passed")
        
        print("Testing async manager lifecycle...")
        await test_async_manager_lifecycle()
        print("✓ Async manager lifecycle test passed")
        
        print("Testing async manager timeout operations...")
        await test_async_manager_timeout_operations()
        print("✓ Async manager timeout operations test passed")
        
        print("All tests passed! 🎉")

    asyncio.run(run_tests())
