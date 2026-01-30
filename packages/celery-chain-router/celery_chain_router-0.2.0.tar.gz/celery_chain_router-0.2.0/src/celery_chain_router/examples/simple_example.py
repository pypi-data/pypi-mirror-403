"""
Simple example demonstrating the chain router.

This example shows how to set up the ChainRouter with a Celery application
and run tasks that will be distributed using consistent hashing for data locality.
"""

import socket
import redis
from celery_chain_router import ChainRouter
from celery_chain_router.examples.tasks import (
    app,
    process_order,
    send_notification,
    analyze_customer,
)

# Create and configure the chain router
# Route by customer_id so all tasks for the same customer go to the same worker
router = ChainRouter(routing_key='customer_id', reset_persistent=True)

# Register workers - use simple names matching the queues
router.register_worker("worker1")
router.register_worker("worker2")
router.register_worker("worker3")

# Set task routes
app.conf.task_routes = router

if __name__ == "__main__":
    """
    Submit example tasks to demonstrate the chain router.

    To run this example:
    1. Start Redis: docker run -d -p 6379:6379 redis
    2. Start workers (in separate terminals):
       - celery -A celery_chain_router.examples.tasks worker -n worker1@%h -Q worker1
       - celery -A celery_chain_router.examples.tasks worker -n worker2@%h -Q worker2
       - celery -A celery_chain_router.examples.tasks worker -n worker3@%h -Q worker3
    3. Run this script: python -m celery_chain_router.examples.simple_example
    """
    # Check if Redis is running
    try:
        s = socket.socket()
        s.connect(('localhost', 6379))
        s.close()
    except Exception:
        print("Error: Redis doesn't appear to be running.")
        print("Start Redis with: docker run -d -p 6379:6379 redis")
        exit(1)

    # Clear Redis to start clean
    print("Clearing Redis...")
    r = redis.Redis(host='localhost', port=6379)
    r.flushall()

    print("Router configured with consistent hashing")
    print(f"Registered workers: {list(router.worker_positions.keys())}")
    print(f"Routing by: customer_id\n")

    # Create a set of customers
    customers = [f"customer_{i}" for i in range(10)]

    print("Submitting order processing tasks...")
    order_results = []

    # Submit multiple orders per customer
    # With consistent hashing, all orders for the same customer go to the same worker
    for order_num in range(100):
        customer_id = customers[order_num % len(customers)]
        order_id = f"order_{order_num}"
        complexity = 1 + (order_num % 3)

        result = process_order.delay(
            order_id=order_id,
            customer_id=customer_id,
            complexity=complexity
        )
        order_results.append((customer_id, result))

        if order_num % 20 == 0:
            print(f"Submitted {order_num} orders...")

    # Wait for order tasks to complete
    print("\nWaiting for orders to complete...")
    completed_orders = []
    for i, (customer_id, result) in enumerate(order_results):
        try:
            data = result.get(timeout=30)
            completed_orders.append(data)
            if i % 20 == 0:
                print(f"Completed {i}/{len(order_results)} orders")
        except Exception as e:
            print(f"Error with order {i}: {e}")

    # Analyze distribution by customer
    print("\n=== Data Locality Analysis ===\n")

    customer_workers = {}
    for order in completed_orders:
        cid = order['customer_id']
        worker = order['worker'].split('@')[0]
        if cid not in customer_workers:
            customer_workers[cid] = set()
        customer_workers[cid].add(worker)

    # Check that each customer's orders went to exactly one worker
    perfect_locality = sum(1 for workers in customer_workers.values() if len(workers) == 1)
    print(f"Customers with perfect locality (all orders to same worker): "
          f"{perfect_locality}/{len(customer_workers)}")

    for cid, workers in sorted(customer_workers.items()):
        status = "OK" if len(workers) == 1 else "SPLIT"
        print(f"  {cid}: {', '.join(workers)} [{status}]")

    # Now send notifications and analyze - should go to same workers
    print("\nSubmitting notification and analysis tasks...")
    followup_results = []

    for customer_id in customers:
        # Send notification
        notif = send_notification.delay(
            customer_id=customer_id,
            message="Your order has been processed!"
        )
        # Analyze customer
        analysis = analyze_customer.delay(customer_id=customer_id)

        followup_results.append((customer_id, 'notification', notif))
        followup_results.append((customer_id, 'analysis', analysis))

    # Wait for followup tasks
    print("Waiting for followup tasks...")
    followup_data = []
    for customer_id, task_type, result in followup_results:
        try:
            data = result.get(timeout=10)
            followup_data.append((customer_id, task_type, data))
        except Exception as e:
            print(f"Error with {task_type} for {customer_id}: {e}")

    # Verify followup tasks went to same workers as orders
    print("\n=== Cross-Task Locality ===\n")
    locality_matches = 0
    total_checks = 0

    for customer_id, task_type, data in followup_data:
        followup_worker = data['worker'].split('@')[0]
        order_workers = customer_workers.get(customer_id, set())

        if order_workers:
            total_checks += 1
            if followup_worker in order_workers:
                locality_matches += 1
            else:
                print(f"  {customer_id} {task_type}: went to {followup_worker}, "
                      f"orders were on {order_workers}")

    if total_checks > 0:
        locality_pct = locality_matches / total_checks * 100
        print(f"Cross-task locality: {locality_matches}/{total_checks} ({locality_pct:.1f}%)")

    # Overall worker distribution
    print("\n=== Worker Distribution ===\n")
    worker_counts = {}
    for order in completed_orders:
        worker = order['worker'].split('@')[0]
        worker_counts[worker] = worker_counts.get(worker, 0) + 1

    for worker, count in sorted(worker_counts.items()):
        pct = count / len(completed_orders) * 100
        print(f"  {worker}: {count} orders ({pct:.1f}%)")

    print("\nExample completed successfully!")
