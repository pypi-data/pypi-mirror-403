from typing import Set, List


class NodeChangeTracker:
    """
    节点变更跟踪器
    用于跟踪节点变更状态，避免重复处理，支持增量变更检测
    """

    def __init__(self, worker_name: str = ""):
        """
        初始化节点变更跟踪器
        :param worker_name: Worker 名称，用于标识
        """
        self.worker_name = worker_name
        self._processing_nodes: Set[str] = set()  # 正在处理的节点
        self._last_nodes: Set[str] = set()  # 上一次的节点列表

    def get_new_nodes(self, current_node_ids: List[str]) -> Set[str]:
        """
        获取新增的节点（增量检测）
        :param current_node_ids: 当前节点ID列表
        :return: 新增的节点ID集合
        """
        current_nodes = set(current_node_ids)

        # 计算新增节点 = 当前节点 - 上次节点 - 正在处理的节点
        new_nodes = current_nodes - self._last_nodes - self._processing_nodes

        # 更新上次节点列表
        self._last_nodes = current_nodes

        return new_nodes

    def mark_processing(self, node_id: str) -> None:
        """
        标记节点为正在处理
        :param node_id: 节点ID
        """
        self._processing_nodes.add(node_id)

    def mark_completed(self, node_id: str) -> None:
        """
        标记节点为已完成
        :param node_id: 节点ID
        """
        self._processing_nodes.discard(node_id)

    def mark_failed(self, node_id: str, remove_from_processing: bool = False) -> None:
        """
        标记节点为失败
        :param node_id: 节点ID
        :param remove_from_processing: 是否从处理列表中移除（默认保留，等待重试）
        """
        if remove_from_processing:
            self._processing_nodes.discard(node_id)

    def is_processing(self, node_id: str) -> bool:
        """
        检查节点是否正在处理
        :param node_id: 节点ID
        :return: 是否正在处理
        """
        return node_id in self._processing_nodes

    def clear_processing(self, node_id: str) -> None:
        """
        清除正在处理的节点标记（用于超时清理等场景）
        :param node_id: 节点ID
        """
        self._processing_nodes.discard(node_id)

    def get_stats(self) -> dict:
        """
        获取统计信息
        :return: 统计信息字典
        """
        return {
            "last_nodes_count": len(self._last_nodes),
            "processing_nodes_count": len(self._processing_nodes),
            "processing_nodes": list(self._processing_nodes),
        }

    def reset(self) -> None:
        """
        重置跟踪器状态
        """
        self._processing_nodes.clear()
        self._last_nodes.clear()
