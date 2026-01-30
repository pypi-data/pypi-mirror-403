import os
import pytest
import json
import tempfile
from celery_chain_router import ChainRouter


class TestChainRouter:
    """Test suite for the ChainRouter class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Create a temporary file for persistent storage
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()

        # Clear shared state between tests
        ChainRouter._shared_worker_positions = {}

        # Create router with test config
        self.router = ChainRouter(
            persistent_file=self.temp_file.name,
            reset_persistent=True
        )

    def teardown_method(self):
        """Clean up after each test method."""
        # Remove temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        # Clear shared state
        ChainRouter._shared_worker_positions = {}

    def test_worker_registration(self):
        """Test that workers can be registered."""
        # Register workers
        self.router.register_worker("worker1")
        self.router.register_worker("worker2")
        self.router.register_worker("worker3")

        # Check that workers are registered
        assert "worker1" in self.router.worker_positions
        assert "worker2" in self.router.worker_positions
        assert "worker3" in self.router.worker_positions

        # Check each worker has virtual node positions
        for worker, positions in self.router.worker_positions.items():
            assert len(positions) == self.router.virtual_nodes

    def test_worker_persistence(self):
        """Test that worker positions are persisted to file."""
        # Register workers
        self.router.register_worker("worker1")
        self.router.register_worker("worker2")

        # Check file exists
        assert os.path.exists(self.temp_file.name)

        # Check file content
        with open(self.temp_file.name, 'r') as f:
            data = json.load(f)
            assert "worker1" in data
            assert "worker2" in data

        # Clear shared state and create new router with same file
        ChainRouter._shared_worker_positions = {}
        new_router = ChainRouter(persistent_file=self.temp_file.name)

        # Check that worker positions are loaded
        assert "worker1" in new_router.worker_positions
        assert "worker2" in new_router.worker_positions

        # Check positions match
        assert new_router.worker_positions["worker1"] == self.router.worker_positions["worker1"]
        assert new_router.worker_positions["worker2"] == self.router.worker_positions["worker2"]

    def test_task_routing_consistency(self):
        """Test that the same task arguments always route to the same worker."""
        # Register workers
        self.router.register_worker("worker1")
        self.router.register_worker("worker2")
        self.router.register_worker("worker3")

        # Route the same task multiple times
        routes = []
        for _ in range(10):
            route = self.router.route_task("my_task", args=("customer_123",))
            routes.append(route["queue"])

        # All routes should be the same
        assert len(set(routes)) == 1, "Same task should always route to same worker"

    def test_routing_key_kwarg(self):
        """Test routing based on a specific kwarg."""
        router = ChainRouter(
            routing_key="customer_id",
            persistent_file=self.temp_file.name,
            reset_persistent=True
        )
        router.register_worker("worker1")
        router.register_worker("worker2")
        router.register_worker("worker3")

        # Tasks with same customer_id should go to same worker
        route1 = router.route_task("task_a", kwargs={"customer_id": "c123", "data": "x"})
        route2 = router.route_task("task_b", kwargs={"customer_id": "c123", "data": "y"})
        route3 = router.route_task("task_a", kwargs={"customer_id": "c123", "data": "z"})

        assert route1["queue"] == route2["queue"] == route3["queue"]

        # Different customer_id may go to different worker
        route4 = router.route_task("task_a", kwargs={"customer_id": "c456", "data": "x"})
        # (We can't assert it's different, as it might hash to the same worker)
        assert "queue" in route4

    def test_routing_key_extractor(self):
        """Test routing with a custom key extractor function."""
        def extract_key(task_name, args, kwargs):
            # Use the first arg for process tasks, second arg for analyze tasks
            if "process" in task_name:
                return args[0] if args else None
            return args[1] if len(args) > 1 else None

        router = ChainRouter(
            routing_key_extractor=extract_key,
            persistent_file=self.temp_file.name,
            reset_persistent=True
        )
        router.register_worker("worker1")
        router.register_worker("worker2")

        # Same first arg for process tasks -> same worker
        route1 = router.route_task("process_data", args=("key123", "other"))
        route2 = router.route_task("process_item", args=("key123", "different"))
        assert route1["queue"] == route2["queue"]

    def test_worker_normalization(self):
        """Test that worker names are properly normalized."""
        # Register worker with hostname
        self.router.register_worker("worker1@host")

        # Check that it's normalized in the worker positions
        assert "worker1" in self.router.worker_positions

        # Route a task
        route = self.router.route_task("task1", args=(1, 2))

        # Check queue name is normalized
        assert route["queue"] == "worker1"

    def test_stats_tracking(self):
        """Test that worker stats are tracked."""
        # Register workers
        self.router.register_worker("worker1")
        self.router.register_worker("worker2")

        # Route tasks
        for i in range(10):
            self.router.route_task(f"task{i}", args=(i,))

        # Get stats
        stats = self.router.get_stats()

        # Check stats are tracked
        assert "worker1" in stats or "worker2" in stats
        assert sum(stats.values()) == 10

    def test_unregister_worker(self):
        """Test that workers can be unregistered."""
        self.router.register_worker("worker1")
        self.router.register_worker("worker2")
        self.router.register_worker("worker3")

        assert len(self.router.worker_positions) == 3

        # Unregister a worker
        result = self.router.unregister_worker("worker2")
        assert result is True
        assert "worker2" not in self.router.worker_positions
        assert len(self.router.worker_positions) == 2

        # Try to unregister non-existent worker
        result = self.router.unregister_worker("worker_nonexistent")
        assert result is False

    def test_get_worker_for_key(self):
        """Test the get_worker_for_key helper method."""
        self.router.register_worker("worker1")
        self.router.register_worker("worker2")

        # Should return consistent results
        worker1 = self.router.get_worker_for_key("test_key_123")
        worker2 = self.router.get_worker_for_key("test_key_123")
        assert worker1 == worker2

    def test_no_workers_returns_none(self):
        """Test that routing returns None when no workers are registered."""
        route = self.router.route_task("some_task", args=(1,))
        assert route is None

    def test_distribution_balance(self):
        """Test that tasks are reasonably balanced across workers."""
        self.router.register_worker("worker1")
        self.router.register_worker("worker2")
        self.router.register_worker("worker3")

        # Route many tasks with different keys
        counts = {"worker1": 0, "worker2": 0, "worker3": 0}
        for i in range(3000):
            route = self.router.route_task("task", args=(f"key_{i}",))
            counts[route["queue"]] += 1

        # Each worker should have roughly 1000 tasks (within 30% tolerance)
        for worker, count in counts.items():
            assert 700 < count < 1300, f"{worker} has {count} tasks, expected ~1000"

    def test_virtual_nodes_customization(self):
        """Test that virtual_nodes parameter works."""
        router = ChainRouter(
            virtual_nodes=50,
            persistent_file=self.temp_file.name,
            reset_persistent=True
        )
        router.register_worker("worker1")

        assert len(router.worker_positions["worker1"]) == 50

    def test_callable_interface(self):
        """Test that router can be called directly (for Celery integration)."""
        self.router.register_worker("worker1")
        self.router.register_worker("worker2")

        # Call router directly like Celery does
        route = self.router("my_task", args=("arg1",), kwargs={"key": "value"})
        assert "queue" in route
        assert route["queue"] in ["worker1", "worker2"]

    def test_graceful_scaling(self):
        """Test that adding a worker only moves ~1/N of keys."""
        self.router.register_worker("worker1")
        self.router.register_worker("worker2")

        # Record routing for 1000 keys
        keys = [f"key_{i}" for i in range(1000)]
        routing_before = {}
        for key in keys:
            route = self.router.route_task("task", args=(key,))
            routing_before[key] = route["queue"]

        # Add a third worker
        self.router.register_worker("worker3")

        # Check how many keys moved
        keys_moved = 0
        for key in keys:
            route = self.router.route_task("task", args=(key,))
            if routing_before[key] != route["queue"]:
                keys_moved += 1

        # With 3 workers, ~1/3 of keys should move (with some tolerance)
        # Allow 20-50% movement (ideal is 33%)
        movement_ratio = keys_moved / len(keys)
        assert 0.15 < movement_ratio < 0.50, f"Movement ratio {movement_ratio} outside expected range"
