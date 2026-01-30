"""
Celery Chain Router Package

This package provides the ChainRouter, a Celery router that uses consistent
hashing to route tasks with the same routing key to the same worker,
enabling data locality and efficient caching.
"""

from celery_chain_router.router import ChainRouter

__version__ = '0.2.0'
__all__ = ['ChainRouter']
