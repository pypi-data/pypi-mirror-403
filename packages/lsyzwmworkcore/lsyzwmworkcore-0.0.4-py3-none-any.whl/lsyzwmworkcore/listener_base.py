import logging
import threading
from typing import Optional
from abc import ABC, abstractmethod

log = logging.getLogger("lsyzwm_work_core")


class ListenerBase(ABC):
    """监听器抽象基类"""

    def __init__(self, listener_id: str, **kwargs) -> None:
        """
        初始化Listener基类
        :param listener_id: 监听器唯一标识
        """
        self.listener_id: str = listener_id
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

    @property
    @abstractmethod
    def listener_name(self) -> str:
        """子类必须实现此属性，返回监听器类型名称"""
        pass

    @abstractmethod
    def _run(self) -> None:
        """
        实际运行逻辑（子类实现）
        此方法在独立线程中运行
        """
        pass

    @abstractmethod
    def _cleanup(self) -> None:
        """
        清理资源（子类实现）
        在 stop() 时调用，用于释放资源
        """
        pass

    def start(self) -> None:
        """启动监听（在独立线程中运行）"""
        if self._running:
            log.warning(f"[{self.listener_id}] 监听器已在运行中")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._thread_wrapper,
            name=f"Listener-{self.listener_id}",
            daemon=True,
        )
        self._thread.start()
        log.info(f"[{self.listener_id}] 监听器已启动")

    def _thread_wrapper(self) -> None:
        """线程包装器，处理异常"""
        try:
            self._run()
        except Exception as ex:
            log.error(f"[{self.listener_id}] 监听器运行异常: {ex}", exc_info=True)
        finally:
            self._running = False
            log.info(f"[{self.listener_id}] 监听器线程已退出")

    def stop(self) -> None:
        """停止监听"""
        if not self._running:
            log.warning(f"[{self.listener_id}] 监听器未在运行")
            return

        log.info(f"[{self.listener_id}] 正在停止监听器...")
        self._running = False

        # 调用子类清理方法
        try:
            self._cleanup()
        except Exception as ex:
            log.error(f"[{self.listener_id}] 清理资源失败: {ex}", exc_info=True)

        # 等待线程结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                log.warning(f"[{self.listener_id}] 线程未能在超时时间内结束")

        log.info(f"[{self.listener_id}] 监听器已停止")

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
