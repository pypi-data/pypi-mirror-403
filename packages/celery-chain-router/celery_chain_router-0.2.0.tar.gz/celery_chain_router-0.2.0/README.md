# Celery Chain Router

A Celery router that uses consistent hashing for intelligent task distribution across workers.

## Overview

The Chain Router provides data locality for Celery tasks by routing tasks with the same routing key to the same worker. This is achieved using consistent hashing with virtual nodes, a proven algorithm used by systems like Redis Cluster and Cassandra.

### Key Features

- **Data Locality**: Tasks with the same routing key always go to the same worker
- **Consistent Hashing**: Industry-standard algorithm for distributed routing
- **Graceful Scaling**: Adding/removing workers only redistributes ~1/N of tasks
- **Flexible Routing Keys**: Route by kwarg name, custom function, or first argument
- **Worker Discovery**: Automatically tracks worker availability via Celery signals

## Why Use Chain Router?

Celery's default routing distributes tasks randomly or round-robin, which can lead to inefficiencies when tasks operate on related data.

### Data Locality Benefits

Consider processing customer orders:

```python
# Without Chain Router: tasks go to random workers
process_order.delay(order_id="o1", customer_id="c123")  # -> worker1
process_order.delay(order_id="o2", customer_id="c123")  # -> worker3
send_receipt.delay(customer_id="c123")                   # -> worker2
# Customer data loaded 3 times on 3 different workers

# With Chain Router: same customer -> same worker
process_order.delay(order_id="o1", customer_id="c123")  # -> worker1
process_order.delay(order_id="o2", customer_id="c123")  # -> worker1
send_receipt.delay(customer_id="c123")                   # -> worker1
# Customer data loaded once, reused from cache
```

This reduces:
- Memory usage (no duplicate data loading)
- Network I/O (data stays local)
- Cache misses (related work uses same cache)

## Installation

```bash
pip install celery-chain-router
```

## Quick Start

```python
from celery import Celery
from celery_chain_router import ChainRouter

app = Celery('myapp', broker='redis://localhost:6379/0')

# Route tasks by customer_id kwarg
router = ChainRouter(routing_key='customer_id')

# Register your workers
router.register_worker("worker1")
router.register_worker("worker2")
router.register_worker("worker3")

# Use the router
app.conf.task_routes = router

@app.task
def process_order(order_id, customer_id):
    # All tasks with same customer_id go to same worker
    pass

@app.task
def send_notification(customer_id, message):
    # Also routed by customer_id
    pass
```

## Configuration Options

### Route by Keyword Argument

The simplest option - specify which kwarg to use as the routing key:

```python
router = ChainRouter(routing_key='customer_id')

# These go to the same worker:
task.delay(data="x", customer_id="c123")
task.delay(data="y", customer_id="c123")
```

### Route by Custom Function

For complex routing logic, provide a function that extracts the key:

```python
def extract_key(task_name, args, kwargs):
    if task_name.startswith('customer.'):
        return kwargs.get('customer_id')
    elif task_name.startswith('order.'):
        return kwargs.get('order_id')
    return None  # Fall back to default routing

router = ChainRouter(routing_key_extractor=extract_key)
```

### Default Behavior

If no routing key is configured:
1. Uses the first positional argument as the key
2. Falls back to task name only (all instances of a task go to same worker)

### All Parameters

```python
router = ChainRouter(
    routing_key='customer_id',           # Kwarg name to route by
    routing_key_extractor=my_function,   # Custom extraction function
    virtual_nodes=150,                   # Virtual nodes per worker (default: 150)
    persistent_file='~/.workers.json',   # File to persist worker positions
    reset_persistent=False,              # Reset persisted state on init
)
```

## How It Works

### Consistent Hashing

1. Each worker is assigned multiple positions on a hash ring (virtual nodes)
2. Tasks are hashed based on their routing key
3. The task is routed to the nearest worker position (clockwise) on the ring

This ensures:
- **Consistency**: Same key always maps to same worker
- **Balance**: Virtual nodes distribute load evenly
- **Stability**: Adding a worker only moves ~1/N of existing keys

### Worker Scaling

When you add or remove workers:

```python
# Start with 2 workers
router.register_worker("worker1")
router.register_worker("worker2")

# Add a third worker
router.register_worker("worker3")
# Only ~33% of keys are redistributed (ideal is 1/3)

# Remove a worker
router.unregister_worker("worker2")
# Only worker2's keys are redistributed
```

## Running the Example

1. Start Redis:
   ```bash
   docker run -d -p 6379:6379 redis
   ```

2. Start workers (in separate terminals):
   ```bash
   celery -A celery_chain_router.examples.tasks worker -n worker1@%h -Q worker1
   celery -A celery_chain_router.examples.tasks worker -n worker2@%h -Q worker2
   celery -A celery_chain_router.examples.tasks worker -n worker3@%h -Q worker3
   ```

3. Run the example:
   ```bash
   python -m celery_chain_router.examples.simple_example
   ```

## Ideal Use Cases

Chain Router excels when:

- Tasks frequently operate on the same entity (customer, order, document)
- Loading data has significant overhead
- Worker-local caching improves performance
- You need predictable, consistent routing

## Utilities

The package includes utilities for testing and analysis:

```python
from celery_chain_router.utils import (
    simulate_task_distribution,
    analyze_routing_consistency,
    analyze_worker_scaling,
    get_key_distribution,
)

# Check distribution balance
stats = simulate_task_distribution(router, num_tasks=1000)
print(stats['worker_counts'])

# Verify routing is consistent
result = analyze_routing_consistency(router, routing_keys=['a', 'b', 'c'])
print(result['is_consistent'])  # True
```

## License

MIT License - See LICENSE file for details.
