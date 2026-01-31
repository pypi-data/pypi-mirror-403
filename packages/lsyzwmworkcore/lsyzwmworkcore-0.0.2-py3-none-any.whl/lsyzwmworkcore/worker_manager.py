import logging
from typing import Dict, List, Optional, Type

from lsyzwmworkcore.base import WorkerBase

log = logging.getLogger("lsyzwm_work_core")


class WorkerManager:
    """
    Worker 管理器（单例模式）

    管理所有 Worker，确保每种 Worker 类型只有一个实例。
    """

    _instance: Optional["WorkerManager"] = None

    def __new__(cls) -> "WorkerManager":
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Worker 类注册表：{worker_name: WorkerClass}
        self._worker_classes: Dict[str, Type[WorkerBase]] = {}
        # Worker 实例存储：{worker_name: worker_instance}
        self._workers: Dict[str, WorkerBase] = {}

    def register_worker_class(self, worker_class: Type[WorkerBase]) -> None:
        """
        注册 Worker 类

        将 Worker 类注册到管理器，同时创建单例实例。

        :param worker_class: Worker 类（必须继承 WorkerBase）
        """
        # 创建 Worker 实例
        worker = worker_class()
        worker_name = worker.worker_name

        if worker_name in self._worker_classes:
            log.warning(f"[WorkerManager] Worker '{worker_name}' 已注册，将被覆盖")

        self._worker_classes[worker_name] = worker_class
        self._workers[worker_name] = worker

    def get_worker(self, name: str) -> Optional[WorkerBase]:
        """
        获取 Worker 实例

        :param name: Worker 名称
        :return: Worker 实例，如果不存在则返回 None
        """
        worker = self._workers.get(name)
        if worker is None:
            log.warning(f"[WorkerManager] Worker '{name}' 不存在")
        return worker

    def get_all_workers(self) -> List[WorkerBase]:
        """
        获取所有 Worker 实例

        :return: Worker 实例列表
        """
        return list(self._workers.values())

    def get_worker_names(self) -> List[str]:
        """
        获取所有已注册的 Worker 名称

        :return: Worker 名称列表
        """
        return list(self._workers.keys())


# 全局单例实例
worker_manager = WorkerManager()
