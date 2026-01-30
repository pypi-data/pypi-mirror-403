"""循环检测器 - 负责识别各种循环结构"""
from dataclasses import dataclass
from typing import List, Optional, Set
import uuid


# 循环节点类型映射
LOOP_NODE_TYPES = {
    'for_statement': 'for',
    'enhanced_for_statement': 'foreach',
    'while_statement': 'while',
    'do_statement': 'while',
}

# Stream 方法名
STREAM_LOOP_METHODS = {'forEach', 'map', 'filter', 'flatMap', 'peek', 'forEachOrdered'}


@dataclass
class LoopInfo:
    """循环信息"""
    loop_id: str             # UUID
    loop_type: str           # 'for', 'foreach', 'while', 'stream'
    start_line: int
    end_line: int
    iterator_var: str = ""   # 循环变量名 (如 for 中的 i, foreach 中的 item)
    collection_var: str = "" # 被遍历的集合变量名 (用于类型推断)


class LoopDetector:
    """循环检测器"""

    def __init__(self):
        """初始化循环检测器"""
        self.loops: List[LoopInfo] = []
        self.content_bytes = None

    def detect_loops(self, method_body_node) -> List[LoopInfo]:
        """
        检测所有传统循环 (for/while/foreach)

        Args:
            method_body_node: 方法体 AST 节点

        Returns:
            循环信息列表
        """
        loops = []

        def traverse(node):
            # 检查是否是循环节点
            if node.type in LOOP_NODE_TYPES:
                loop_type = LOOP_NODE_TYPES[node.type]
                loop_info = LoopInfo(
                    loop_id=str(uuid.uuid4()),
                    loop_type=loop_type,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1
                )

                # 提取循环变量（如果是 foreach）
                if node.type == 'enhanced_for_statement' and len(node.children) > 2:
                    # enhanced_for: for (Type var : collection)
                    name_node = node.children[2] if len(node.children) > 2 else None
                    if name_node and name_node.type == 'identifier':
                        loop_info.iterator_var = self._get_text(name_node)

                    # 提取被遍历的集合
                    if len(node.children) > 4:
                        collection_node = node.children[4]
                        if collection_node.type == 'identifier':
                            loop_info.collection_var = self._get_text(collection_node)

                loops.append(loop_info)

            # 继续遍历子节点
            for child in node.children:
                traverse(child)

        traverse(method_body_node)
        self.loops.extend(loops)
        return loops

    def detect_stream_chains(self, method_body_node) -> List[LoopInfo]:
        """
        检测 stream 链式调用

        识别模式:
        - collection.stream().forEach(...)
        - list.stream().map(...).filter(...)

        Args:
            method_body_node: 方法体 AST 节点

        Returns:
            stream 循环信息列表
        """
        stream_loops = []

        def traverse(node):
            # 检查方法调用
            if node.type == 'method_invocation':
                method_name = self._extract_method_name(node)
                if method_name in STREAM_LOOP_METHODS:
                    # 这是一个 stream 循环方法
                    loop_info = LoopInfo(
                        loop_id=str(uuid.uuid4()),
                        loop_type='stream',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1
                    )
                    stream_loops.append(loop_info)

            # 继续遍历子节点
            for child in node.children:
                traverse(child)

        traverse(method_body_node)
        self.loops.extend(stream_loops)
        return stream_loops

    def get_loop_at_line(self, line: int) -> Optional[LoopInfo]:
        """
        获取指定行所在的循环

        Args:
            line: 行号

        Returns:
            循环信息，如果不在循环内则返回 None
        """
        for loop in self.loops:
            if loop.start_line <= line <= loop.end_line:
                return loop
        return None

    def is_in_loop(self, line: int) -> bool:
        """
        判断某行是否在循环内

        Args:
            line: 行号

        Returns:
            True 如果在循环内，否则 False
        """
        return self.get_loop_at_line(line) is not None

    def _extract_method_name(self, method_invocation_node) -> str:
        """从 method_invocation 节点提取方法名"""
        for child in method_invocation_node.children:
            if child.type == 'identifier':
                return self._get_text(child)
        return ""

    def _get_text(self, node) -> str:
        """获取节点文本"""
        if self.content_bytes and hasattr(node, 'start_byte'):
            return self.content_bytes[node.start_byte:node.end_byte].decode('utf-8')
        return ""

    def set_content_bytes(self, content_bytes: bytes):
        """设置内容字节（用于文本提取）"""
        self.content_bytes = content_bytes
