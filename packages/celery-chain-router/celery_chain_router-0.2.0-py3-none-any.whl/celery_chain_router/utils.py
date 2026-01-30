"""Utility functions for the chain router."""

from typing import Dict, List, Any, Optional
from collections import Counter


def simulate_task_distribution(
    router,
    num_tasks: int = 1000,
    routing_keys: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Simulate distributing tasks and analyze the distribution.

    Args:
        router: An instance of ChainRouter
        num_tasks: Number of tasks to simulate
        routing_keys: Optional list of routing keys to use. If None, uses
                      sequential integers (0, 1, 2, ...). If provided, keys
                      are cycled through.

    Returns:
        Dictionary with distribution statistics
    """
    task_counts = {worker: 0 for worker in router.worker_positions}

    for i in range(num_tasks):
        # Determine the routing key
        if routing_keys:
            key = routing_keys[i % len(routing_keys)]
            task_args = (key,)
        else:
            task_args = (i,)

        # Route the task
        route = router.route_task("simulated_task", task_args)
        if route:
            worker = route.get('queue')
            if worker in task_counts:
                task_counts[worker] += 1

    # Calculate distribution statistics
    counts = list(task_counts.values())
    total = sum(counts)
    avg = total / len(counts) if counts else 0
    variance = sum((c - avg) ** 2 for c in counts) / len(counts) if counts else 0
    std_dev = variance ** 0.5

    return {
        'worker_counts': task_counts,
        'total_tasks': total,
        'average_per_worker': avg,
        'std_deviation': std_dev,
        'min_tasks': min(counts) if counts else 0,
        'max_tasks': max(counts) if counts else 0,
    }


def analyze_routing_consistency(
    router,
    routing_keys: List[Any],
    iterations: int = 100
) -> Dict[str, Any]:
    """
    Verify that routing is consistent (same key always goes to same worker).

    Args:
        router: An instance of ChainRouter
        routing_keys: List of routing keys to test
        iterations: Number of times to route each key

    Returns:
        Dictionary with consistency analysis
    """
    inconsistencies = []

    for key in routing_keys:
        workers_seen = set()
        for _ in range(iterations):
            route = router.route_task("test_task", (key,))
            if route:
                workers_seen.add(route['queue'])

        if len(workers_seen) > 1:
            inconsistencies.append({
                'key': key,
                'workers': list(workers_seen)
            })

    return {
        'is_consistent': len(inconsistencies) == 0,
        'keys_tested': len(routing_keys),
        'inconsistencies': inconsistencies
    }


def analyze_worker_scaling(
    router,
    new_worker_name: str,
    sample_keys: List[Any]
) -> Dict[str, Any]:
    """
    Analyze how adding a new worker affects key distribution.

    This helps verify that consistent hashing minimizes redistribution.

    Args:
        router: An instance of ChainRouter
        new_worker_name: Name of the worker to add
        sample_keys: List of keys to track

    Returns:
        Dictionary with scaling analysis
    """
    # Record current routing
    routing_before = {}
    for key in sample_keys:
        route = router.route_task("test_task", (key,))
        routing_before[key] = route['queue'] if route else None

    # Add new worker
    router.register_worker(new_worker_name)

    # Record new routing
    routing_after = {}
    keys_moved = 0
    for key in sample_keys:
        route = router.route_task("test_task", (key,))
        routing_after[key] = route['queue'] if route else None
        if routing_before[key] != routing_after[key]:
            keys_moved += 1

    # Calculate expected movement (ideal is 1/N where N is new worker count)
    num_workers = len(router.worker_positions)
    expected_movement = 1.0 / num_workers if num_workers > 0 else 0
    actual_movement = keys_moved / len(sample_keys) if sample_keys else 0

    return {
        'keys_tested': len(sample_keys),
        'keys_moved': keys_moved,
        'movement_ratio': actual_movement,
        'expected_ratio': expected_movement,
        'efficiency': 1 - abs(actual_movement - expected_movement) / expected_movement
                      if expected_movement > 0 else 1.0
    }


def get_key_distribution(router, routing_keys: List[Any]) -> Dict[str, List[Any]]:
    """
    Get which worker each routing key maps to.

    Args:
        router: An instance of ChainRouter
        routing_keys: List of routing keys to check

    Returns:
        Dictionary mapping worker names to lists of keys they handle
    """
    distribution: Dict[str, List[Any]] = {
        worker: [] for worker in router.worker_positions
    }

    for key in routing_keys:
        route = router.route_task("test_task", (key,))
        if route:
            worker = route['queue']
            if worker in distribution:
                distribution[worker].append(key)

    return distribution
