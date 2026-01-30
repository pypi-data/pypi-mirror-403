"""
Task definitions for the chain router example.
"""
from celery import Celery
import os
import time

# Create the Celery app with explicit name matching the module
app = Celery('celery_chain_router.examples.tasks')
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True,
)


@app.task(bind=True, name='celery_chain_router.examples.tasks.process_order')
def process_order(self, order_id, customer_id, complexity=1):
    """
    Process an order for a customer.

    With ChainRouter configured with routing_key='customer_id',
    all orders for the same customer go to the same worker.
    """
    worker_name = self.request.hostname or os.environ.get('HOSTNAME', 'unknown')

    # Simulate work proportional to complexity
    time.sleep(0.1 * complexity)

    return {
        'order_id': order_id,
        'customer_id': customer_id,
        'worker': worker_name,
        'complexity': complexity,
        'status': 'processed'
    }


@app.task(bind=True, name='celery_chain_router.examples.tasks.send_notification')
def send_notification(self, customer_id, message):
    """
    Send a notification to a customer.

    With ChainRouter, this goes to the same worker that processed
    the customer's orders, enabling data locality.
    """
    worker_name = self.request.hostname or os.environ.get('HOSTNAME', 'unknown')

    # Simulate notification work
    time.sleep(0.05)

    return {
        'customer_id': customer_id,
        'worker': worker_name,
        'message': message,
        'status': 'sent'
    }


@app.task(bind=True, name='celery_chain_router.examples.tasks.analyze_customer')
def analyze_customer(self, customer_id):
    """
    Analyze a customer's activity.

    This task benefits from data locality - if the customer's data
    was already loaded by previous tasks on this worker.
    """
    worker_name = self.request.hostname or os.environ.get('HOSTNAME', 'unknown')

    # Simulate analysis work
    time.sleep(0.05)

    return {
        'customer_id': customer_id,
        'worker': worker_name,
        'status': 'analyzed'
    }
