import hashlib
import bisect
import os
import json
from celery import signals
from typing import Dict, Any, Optional, List, Callable, Tuple, Union


class ChainRouter:
    """
    A Celery router that uses consistent hashing for task distribution.

    This router distributes tasks across workers using consistent hashing,
    providing data locality by routing tasks with the same routing key
    to the same worker.

    Attributes:
        routing_key (str): The kwarg name to use as routing key
        routing_key_extractor (callable): Function to extract routing key from task args
        virtual_nodes (int): Number of virtual nodes per worker for distribution
    """

    _shared_worker_positions = {}

    def __init__(
        self,
        routing_key: Optional[str] = None,
        routing_key_extractor: Optional[Callable[[str, tuple, dict], Any]] = None,
        virtual_nodes: int = 150,
        persistent_file: Optional[str] = None,
        reset_persistent: bool = False
    ):
        """
        Initialize the chain router.

        Args:
            routing_key: Name of the kwarg to use as routing key (e.g., 'customer_id').
                         If provided, tasks will be routed based on this kwarg's value.
            routing_key_extractor: A function that takes (task_name, args, kwargs) and
                                   returns the routing key. Use this for complex routing logic.
            virtual_nodes: Number of virtual nodes per worker (higher = better distribution,
                          but more memory). Default: 150
            persistent_file: Path to file for persisting worker positions
            reset_persistent: Whether to reset the persistent storage on init
        """
        self.routing_key = routing_key
        self.routing_key_extractor = routing_key_extractor
        self.virtual_nodes = virtual_nodes
        self.persistent_file = persistent_file or os.path.expanduser(
            "~/.chain_router_workers.json"
        )

        # The hash ring: sorted list of (position, worker_name)
        self.ring: List[Tuple[int, str]] = []
        self.ring_positions: List[int] = []  # Just positions for binary search

        # Worker tracking
        self.worker_positions: Dict[str, List[int]] = {}  # worker -> list of positions
        self.worker_stats: Dict[str, int] = {}

        if reset_persistent and os.path.exists(self.persistent_file):
            try:
                os.remove(self.persistent_file)
                self.__class__._shared_worker_positions = {}
            except Exception as e:
                print(f"Error resetting persistent storage: {e}")

        self._load_worker_positions()
        self._register_signals()

    def _hash_key(self, key: str) -> int:
        """
        Hash a key to a position on the ring (0 to 2^32-1).

        Uses SHA256 for good distribution properties.
        """
        hash_bytes = hashlib.sha256(key.encode()).digest()
        # Use first 4 bytes as unsigned 32-bit integer
        return int.from_bytes(hash_bytes[:4], byteorder='big')

    def _get_routing_key(
        self, task_name: str, args: Optional[tuple], kwargs: Optional[dict]
    ) -> str:
        """
        Extract the routing key from task arguments.

        Priority:
        1. Use routing_key_extractor if provided
        2. Use routing_key kwarg name if provided
        3. Fall back to first positional arg
        4. Fall back to task name only
        """
        args = args or ()
        kwargs = kwargs or {}

        # Option 1: Custom extractor function
        if self.routing_key_extractor is not None:
            try:
                key = self.routing_key_extractor(task_name, args, kwargs)
                if key is not None:
                    return str(key)
            except Exception:
                pass  # Fall through to other options

        # Option 2: Extract from kwargs by name
        if self.routing_key is not None:
            key = kwargs.get(self.routing_key)
            if key is not None:
                return str(key)

        # Option 3: Use first positional arg (include task name to differentiate)
        if args:
            return f"{task_name}:{args[0]}"

        # Option 4: Task name only (all instances of this task go to same worker)
        return task_name

    def _normalize_worker_name(self, worker_name: str) -> str:
        """Extract just the worker name without hostname."""
        return worker_name.split('@')[0] if '@' in worker_name else worker_name

    def _build_ring(self) -> None:
        """Rebuild the hash ring from current worker positions."""
        ring = []
        for worker, positions in self.worker_positions.items():
            for pos in positions:
                ring.append((pos, worker))

        # Sort by position for binary search
        ring.sort(key=lambda x: x[0])

        self.ring = ring
        self.ring_positions = [pos for pos, _ in ring]

    def _load_worker_positions(self) -> None:
        """Load worker positions from persistent storage if available."""
        # First use class-level storage
        self.worker_positions = {
            k: list(v) for k, v in self.__class__._shared_worker_positions.items()
        }

        try:
            if os.path.exists(self.persistent_file):
                with open(self.persistent_file, 'r') as f:
                    stored_data = json.load(f)

                    # Normalize worker names and load positions
                    normalized_positions = {}
                    for worker, positions in stored_data.items():
                        normalized_name = self._normalize_worker_name(worker)
                        normalized_positions[normalized_name] = positions

                    self.worker_positions = normalized_positions
                    self.__class__._shared_worker_positions = {
                        k: list(v) for k, v in normalized_positions.items()
                    }
        except Exception as e:
            print(f"Error loading worker positions: {e}")

        self._build_ring()

    def _save_worker_positions(self) -> None:
        """Save worker positions to persistent storage."""
        try:
            with open(self.persistent_file, 'w') as f:
                json.dump(self.worker_positions, f)
        except Exception as e:
            print(f"Error saving worker positions: {e}")

    def _find_worker_on_ring(self, key_hash: int) -> Optional[str]:
        """
        Find the worker responsible for a given hash using the consistent hash ring.

        Uses binary search to find the first position >= key_hash,
        wrapping around to the first position if necessary.
        """
        if not self.ring:
            return None

        # Binary search for the first position >= key_hash
        idx = bisect.bisect_left(self.ring_positions, key_hash)

        # Wrap around if we're past the end
        if idx >= len(self.ring):
            idx = 0

        return self.ring[idx][1]

    def register_worker(self, worker_name: str) -> List[int]:
        """
        Register a worker and assign its virtual node positions.

        Args:
            worker_name: Name of the worker to register

        Returns:
            List of positions assigned to the worker
        """
        normalized_name = self._normalize_worker_name(worker_name)

        if normalized_name not in self.worker_positions:
            # Generate virtual node positions
            positions = []
            for i in range(self.virtual_nodes):
                virtual_key = f"{normalized_name}:{i}"
                pos = self._hash_key(virtual_key)
                positions.append(pos)

            self.worker_positions[normalized_name] = positions
            self.__class__._shared_worker_positions[normalized_name] = list(positions)
            self.worker_stats[normalized_name] = 0

            self._build_ring()
            self._save_worker_positions()

            return positions

        return self.worker_positions[normalized_name]

    def unregister_worker(self, worker_name: str) -> bool:
        """
        Unregister a worker and remove its virtual nodes from the ring.

        Args:
            worker_name: Name of the worker to unregister

        Returns:
            True if worker was removed, False if worker wasn't registered
        """
        normalized_name = self._normalize_worker_name(worker_name)

        if normalized_name in self.worker_positions:
            del self.worker_positions[normalized_name]
            if normalized_name in self.__class__._shared_worker_positions:
                del self.__class__._shared_worker_positions[normalized_name]
            if normalized_name in self.worker_stats:
                del self.worker_stats[normalized_name]

            self._build_ring()
            self._save_worker_positions()
            return True

        return False

    def _register_signals(self) -> None:
        """Register Celery signals for worker monitoring."""
        router_instance = self

        @signals.worker_ready.connect
        def on_worker_ready(sender, **kwargs):
            hostname = sender.hostname
            normalized_name = router_instance._normalize_worker_name(hostname)
            router_instance.register_worker(normalized_name)

    def __call__(
        self,
        task_name: str,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        options: Optional[dict] = None,
        **kw
    ) -> Optional[Dict[str, str]]:
        """
        Make the router callable directly by Celery.

        Args:
            task_name: Name of the task (string)
            args: Task positional arguments
            kwargs: Task keyword arguments
            options: Additional options dict
            **kw: Additional keyword arguments

        Returns:
            Dict with queue name or None for default routing
        """
        return self.route_task(task_name, args, kwargs, options)

    def route_task(
        self,
        task_name: str,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        options: Optional[dict] = None
    ) -> Optional[Dict[str, str]]:
        """
        Route a task to the appropriate worker based on consistent hashing.

        Args:
            task_name: Name of the task (string)
            args: Task positional arguments
            kwargs: Task keyword arguments
            options: Additional options dict

        Returns:
            Dict with queue name or None for default routing
        """
        # Reload worker positions to ensure we have the latest
        self._load_worker_positions()

        if not self.worker_positions:
            return None

        # Get routing key and hash it
        routing_key = self._get_routing_key(task_name, args, kwargs)
        key_hash = self._hash_key(routing_key)

        # Find worker on the ring
        worker = self._find_worker_on_ring(key_hash)

        if worker:
            self.worker_stats[worker] = self.worker_stats.get(worker, 0) + 1
            return {'queue': worker}

        return None

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about task distribution."""
        return self.worker_stats.copy()

    def get_worker_for_key(self, key: Any) -> Optional[str]:
        """
        Get the worker that would handle a given routing key.

        Useful for debugging or understanding routing behavior.

        Args:
            key: The routing key value

        Returns:
            Worker name or None if no workers registered
        """
        key_hash = self._hash_key(str(key))
        return self._find_worker_on_ring(key_hash)
