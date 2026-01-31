import logging
import threading
from typing import Optional, Dict

from lsyzwmworkcore.listener_base import ListenerBase

log = logging.getLogger("lsyzwm_work_core")


class ListenerManager:
    """全局监听器管理器（单例模式）"""

    _instance: Optional["ListenerManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ListenerManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._listeners = {}  # listener_id -> ListenerBase
                    cls._instance._listeners_lock = threading.Lock()
        return cls._instance

    def start_listener(self, listener: ListenerBase) -> bool:
        """
        启动监听器
        :param listener: 监听器实例
        :return: 是否成功启动
        """
        with self._listeners_lock:
            if listener.listener_id in self._listeners:
                existing = self._listeners[listener.listener_id]
                if existing.is_running:
                    log.warning(f"[ListenerManager] 监听器 {listener.listener_id} 已存在且正在运行")
                    return False
                else:
                    # 移除已停止的监听器
                    del self._listeners[listener.listener_id]

            self._listeners[listener.listener_id] = listener

        try:
            listener.start()
            log.info(f"[ListenerManager] 已启动监听器: {listener.listener_id}")
            return True
        except Exception as ex:
            log.error(f"[ListenerManager] 启动监听器失败: {ex}", exc_info=True)
            with self._listeners_lock:
                self._listeners.pop(listener.listener_id, None)
            return False

    def stop_listener(self, listener_id: str) -> bool:
        """
        停止监听器
        :param listener_id: 监听器ID
        :return: 是否成功停止
        """
        with self._listeners_lock:
            listener = self._listeners.get(listener_id)
            if not listener:
                log.warning(f"[ListenerManager] 监听器 {listener_id} 不存在")
                return False

        try:
            listener.stop()
            with self._listeners_lock:
                self._listeners.pop(listener_id, None)
            log.info(f"[ListenerManager] 已停止监听器: {listener_id}")
            return True
        except Exception as ex:
            log.error(f"[ListenerManager] 停止监听器失败: {ex}", exc_info=True)
            return False

    def get_listener(self, listener_id: str) -> Optional[ListenerBase]:
        """
        获取监听器实例
        :param listener_id: 监听器ID
        :return: 监听器实例或 None
        """
        with self._listeners_lock:
            return self._listeners.get(listener_id)

    def list_listeners(self) -> Dict[str, dict]:
        """
        列出所有监听器状态
        :return: {listener_id: {name, is_running}}
        """
        with self._listeners_lock:
            return {
                lid: {
                    "name": listener.listener_name,
                    "is_running": listener.is_running,
                }
                for lid, listener in self._listeners.items()
            }

    def stop_all(self) -> None:
        """停止所有监听器"""
        log.info("[ListenerManager] 正在停止所有监听器...")
        with self._listeners_lock:
            listener_ids = list(self._listeners.keys())

        for listener_id in listener_ids:
            try:
                self.stop_listener(listener_id)
            except Exception as ex:
                log.error(f"[ListenerManager] 停止监听器 {listener_id} 失败: {ex}")

        log.info("[ListenerManager] 所有监听器已停止")

    @property
    def active_count(self) -> int:
        """获取活跃监听器数量"""
        with self._listeners_lock:
            return sum(1 for l in self._listeners.values() if l.is_running)


# 全局单例实例
listener_manager = ListenerManager()
