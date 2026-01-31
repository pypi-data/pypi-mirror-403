"""
lsyzwmworkcore - 简化 Worker 任务分发与执行的核心库

基于 ZooKeeper 实现分布式任务调度。
"""

from lsyzwmworkcore.base import WorkerBase
from lsyzwmworkcore.node_change_tracker import NodeChangeTracker
from lsyzwmworkcore.worker_manager import WorkerManager, worker_manager

__version__ = "0.0.3"

__all__ = [
    "WorkerBase",
    "NodeChangeTracker",
    "WorkerManager",
    "worker_manager",
]
