import datetime
import random
import time
from typing import List, Optional, Union, Dict
from abc import ABC, abstractmethod

from lsyzwm_master_sdk import MasterZooClient
from twisted.internet import reactor

from kazoo.recipe.watchers import ChildrenWatch

from lsyzwmworkcore.node_change_tracker import NodeChangeTracker


class WorkerBase(ABC):
    def __init__(self, sid: int, zk_client: MasterZooClient) -> None:
        """
        初始化Worker基类
        :param sid: worker实例ID
        :param zk_client: MasterZooClient实例
        """
        self.sid: int = sid
        self.zk_client: MasterZooClient = zk_client

        # 唯一标识 worker 实例
        self.worker_id: str = f"{self.worker_name}-{self.sid}"

        # 初始化节点变更跟踪器
        self.task_tracker = NodeChangeTracker(worker_name=self.worker_name)

    @property
    @abstractmethod
    def worker_name(self) -> str:
        """子类必须实现此属性，返回 worker 名称"""
        pass

    def process_tasks(self, task_ids: List[str]) -> None:
        """批量处理任务（框架方法，不建议重载）"""
        for task_id in task_ids:
            self.on_task_started(task_id)
            try:
                self.process_task(task_id)
                self.on_task_completed(task_id)
            except Exception as ex:
                self.on_task_failed(task_id, ex)

    def on_task_started(self, task_id: str) -> None:
        """
        任务开始钩子，子类可重载以添加自定义逻辑。

        默认行为：标记任务为处理中。
        重载时可调用 super().on_task_started(task_id) 保留默认行为，
        或完全自定义。

        :param task_id: 任务ID
        """
        self.task_tracker.mark_processing(task_id)

    def on_task_completed(self, task_id: str) -> None:
        """
        任务完成钩子，子类可重载以添加自定义逻辑。

        默认行为：标记完成并删除任务节点。
        重载时可调用 super().on_task_completed(task_id) 保留默认行为，
        或完全自定义（如不删除节点）。

        :param task_id: 任务ID
        """
        self.task_tracker.mark_completed(task_id)
        self.delete_task_node(task_id)

    def on_task_failed(self, task_id: str, exception: Exception = None) -> None:
        """
        任务失败钩子，子类可重载以添加自定义逻辑。

        默认行为：标记失败并删除任务节点。
        重载时可调用 super().on_task_failed(task_id, exception) 保留默认行为，
        或完全自定义（如不删除节点、记录日志、发送告警等）。

        :param task_id: 任务ID
        :param exception: 异常对象
        """
        self.task_tracker.mark_failed(task_id, remove_from_processing=True)
        self.delete_task_node(task_id)

    @abstractmethod
    def process_task(self, task_id: str) -> None:
        """
        处理单个任务（子类必须实现）。

        :param task_id: 任务ID
        """
        pass

    def generate_task_id(self) -> str:
        """生成唯一任务ID，格式: {时间戳}_{worker_name}_{sid}_{随机数}"""
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        rand_suffix = random.randint(1000, 9999)
        return f"{timestamp}_{self.worker_name}_{self.sid}_{rand_suffix}"

    def register(self) -> None:
        """注册 worker 实例（创建临时节点）"""
        self.zk_client.register_worker(self.worker_name, self.sid)

    def tasks_change(self, task_ids: List[str]) -> None:
        new_tasks = self.task_tracker.get_new_nodes(task_ids)
        if not new_tasks:
            return

        # 将处理调度到 reactor 线程
        reactor.callFromThread(self.process_tasks, new_tasks)

    def watch_tasks(self) -> ChildrenWatch:
        """监听 worker 实例的任务节点变化"""
        return self.zk_client.watch_worker_tasks(self.worker_name, self.sid, self.tasks_change)

    def get_task_value(self, task_id: str, as_json: bool = False) -> Optional[Union[str, Dict]]:
        """
        获取任务节点值
        :param task_id: 任务ID
        :param as_json: 是否解析为JSON对象，默认为False
        :return: 任务节点数据(字符串或字典)，如果节点不存在则返回None
        """
        return self.zk_client.get_worker_instance_task(self.worker_name, self.sid, task_id, as_json=as_json)

    def delete_task_node(self, task_id: str) -> None:
        """
        删除任务节点
        :param task_id: 任务ID
        """
        self.zk_client.remove_worker_instance_task(self.worker_name, self.sid, task_id)

    def add_task_node(
        self, worker_name: str, payload: Optional[Union[str, Dict]] = None, worker_sid: Optional[int] = None, task_id: Optional[str] = None, task_type: str = "random"
    ) -> None:
        """
        添加任务节点
        :param worker_name: 目标worker名称
        :param payload: 任务节点数据(字符串或字典，可以为None)
        :param worker_sid: 目标worker实例ID，可选
        :param task_id: 任务ID,可选
        :param task_type: 任务类型，默认'random'
        """
        if task_id is None:
            task_id = self.generate_task_id()

        self.zk_client.add_task_node(worker_name, task_id, payload, worker_sid, task_type)

    def add_self_task_node(self, worker_name: str, payload: Optional[Union[str, Dict]] = None, task_id: Optional[str] = None, task_type: str = "random") -> None:
        """
        添加自身任务节点
        :param worker_name: 目标worker名称
        :param payload: 任务节点数据(字符串或字典，可以为None)
        :param task_id: 任务ID,可选
        :param task_type: 任务类型，默认'random'
        """
        worker_sid = self.sid
        self.add_task_node(worker_name, payload, worker_sid, task_id, task_type)

    def get_worker_cache_value(self, cache_id: str, as_json: bool = False) -> Optional[Union[str, Dict]]:
        """
        获取worker缓存节点值
        :param cache_id: 缓存ID
        :param as_json: 是否解析为JSON对象，默认为False
        :return: 缓存节点数据(字符串或字典)，如果节点不存在则返回None
        """
        return self.zk_client.get_worker_cache_value(self.worker_name, cache_id, as_json=as_json)

    def get_worker_instance_cache_value(self, cache_id: str, as_json: bool = False) -> Optional[Union[str, Dict]]:
        """
        获取worker实例缓存节点值
        :param cache_id: 缓存ID
        :param as_json: 是否解析为JSON对象，默认为False
        :return: 缓存节点数据(字符串或字典)，如果节点不存在则返回None
        """
        return self.zk_client.get_worker_instance_cache_value(self.worker_name, self.sid, cache_id, as_json=as_json)

    def set_worker_cache_value(self, cache_id: str, payload: Optional[Union[str, Dict]] = None) -> None:
        """
        设置worker缓存节点值(不存在则创建，存在则更新)
        :param cache_id: 缓存ID
        :param payload: 节点数据(字符串或字典，可以为None)
        """
        self.zk_client.set_worker_cache_value(self.worker_name, cache_id, payload)

    def set_worker_instance_cache_value(self, cache_id: str, payload: Optional[Union[str, Dict]] = None) -> None:
        """
        设置worker实例缓存节点值(不存在则创建，存在则更新)
        :param cache_id: 缓存ID
        :param payload: 节点数据(字符串或字典，可以为None)
        """
        self.zk_client.set_worker_instance_cache_value(self.worker_name, self.sid, cache_id, payload)

    def create_delay_job_node(self, job_id: str, worker_name: str, payload: Dict, delay_ts: int, who: str, worker_sid: Optional[int] = None, task_type: str = "random"):
        """
        创建延时任务节点
        :param job_id: 任务ID
        :param worker_name: worker名称
        :param payload: 任务负载数据
        :param delay_ts: 延迟时间戳
        :param who: 创建者标识
        :param worker_sid: worker实例ID，可选
        :param task_type: 任务类型，默认'random'
        :return: 生成的 master task_id
        """
        return self.zk_client.create_delay_job_node(job_id, worker_name, payload, delay_ts, who, worker_sid, task_type)

    def create_cron_job_node(
        self,
        job_id: str,
        worker_name: str,
        payload: Dict,
        cron: str,
        who: str,
        start_date_ts: Optional[int] = None,
        end_date_ts: Optional[int] = None,
        worker_sid: Optional[int] = None,
        task_type: str = "random",
    ):
        """
        创建Cron定时任务节点
        :param job_id: 任务ID
        :param worker_name: worker名称
        :param payload: 任务负载数据
        :param cron: cron表达式
        :param who: 创建者标识
        :param start_date_ts: 任务开始时间（秒级时间戳），可选
        :param end_date_ts: 任务结束时间（秒级时间戳），可选
        :param worker_sid: worker实例ID，可选
        :param task_type: 任务类型，默认'random'
        :return: 生成的 master task_id
        """
        return self.zk_client.create_cron_job_node(job_id, worker_name, payload, cron, who, start_date_ts, end_date_ts, worker_sid, task_type)

    def create_interval_job_node(
        self,
        job_id: str,
        worker_name: str,
        payload: Dict,
        who: str,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        start_date_ts: Optional[int] = None,
        end_date_ts: Optional[int] = None,
        worker_sid: Optional[int] = None,
        task_type: str = "random",
    ):
        """
        创建间隔任务节点
        :param job_id: 任务ID
        :param worker_name: worker名称
        :param payload: 任务负载数据
        :param who: 创建者标识
        :param weeks: 间隔周数，默认0
        :param days: 间隔天数，默认0
        :param hours: 间隔小时数，默认0
        :param minutes: 间隔分钟数，默认0
        :param seconds: 间隔秒数，默认0
        :param start_date_ts: 任务开始时间（秒级时间戳），可选
        :param end_date_ts: 任务结束时间（秒级时间戳），可选
        :param worker_sid: worker实例ID，可选
        :param task_type: 任务类型，默认'random'
        :return: 生成的 master task_id
        """
        return self.zk_client.create_interval_job_node(job_id, worker_name, payload, who, weeks, days, hours, minutes, seconds, start_date_ts, end_date_ts, worker_sid, task_type)

    def create_remove_job_node(self, job_id: str, who: str):
        """
        创建移除任务节点
        :param job_id: 作业ID
        :param who: 创建者标识
        :return: 生成的 master task_id
        """
        return self.zk_client.create_remove_job_node(job_id, who)

    def delete_client_task(self, worker_name: str, worker_sid: int, task_id: str, who: str):
        """
        删除客户端任务
        :param worker_name: worker名称
        :param worker_sid: worker实例ID
        :param task_id: 任务ID
        :param who: 创建者标识
        :return: 生成的 master task_id
        """
        return self.zk_client.delete_client_task(worker_name, worker_sid, task_id, who)

    def schedule_delete_task(self, task_id: str, hour: int, minute: int):
        """
        创建定时删除当前任务的调度任务（只执行一次）

        :param task_id: 要删除的任务ID
        :param hour: 执行小时（0-23）
        :param minute: 执行分钟（0-59）
        :return: 生成的 master task_id
        """
        # 获取当前交易日作为任务标识
        trading_day = datetime.datetime.now().strftime("%Y%m%d")
        delete_job_id = f"delete_{self.worker_name}_{task_id}_{trading_day}"

        delete_payload = {
            "task_id": task_id,
            "worker_name": self.worker_name,
            "worker_sid": self.sid,
        }

        # 计算今天指定时间的时间戳
        today = datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        delete_ts = int(today.timestamp())

        # cron 表达式：分 时 日 月 周（5字段格式）
        cron = f"{minute} {hour} * * *"

        return self.create_cron_job_node(
            job_id=delete_job_id,
            worker_name="task_delete",
            payload=delete_payload,
            cron=cron,
            who=self.worker_id,
            start_date_ts=delete_ts,
            end_date_ts=delete_ts + 60,  # 结束时间比开始时间晚1分钟，确保只执行一次
        )
