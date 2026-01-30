"""分支检测器 - 负责识别 if/switch 等分支结构"""
from dataclasses import dataclass
from typing import List, Optional
import uuid


# 分支节点类型映射
BRANCH_NODE_TYPES = {
    'if_statement': 'if',
    'switch_statement': 'switch',
    'switch_expression': 'switch',  # Java 14+ switch表达式
}


@dataclass
class BranchInfo:
    """分支信息"""
    branch_id: str           # UUID - 同一个 if-else 链共享
    branch_type: str         # 'if', 'else-if', 'else', 'case', 'default'
    branch_order: int        # 分支顺序: 1, 2, 3...
    condition: Optional[str] # 条件表达式
    start_line: int
    end_line: int


class BranchDetector:
    """分支检测器"""

    def __init__(self):
        """初始化分支检测器"""
        self.branches: List[BranchInfo] = []
        self.content_bytes = None

    def detect_branches(self, method_body_node) -> List[BranchInfo]:
        """
        检测所有分支结构 (if/switch)

        Args:
            method_body_node: 方法体 AST 节点

        Returns:
            分支信息列表
        """
        branches = []

        def traverse(node):
            # 检查 if 语句
            if node.type == 'if_statement':
                branches_in_if = self._extract_if_branches(node)
                branches.extend(branches_in_if)
                # 不继续遍历子节点,因为已经在 _extract_if_branches 中处理

            # 检查 switch 语句或表达式
            elif node.type in ('switch_statement', 'switch_expression'):
                branches_in_switch = self._extract_switch_branches(node)
                branches.extend(branches_in_switch)
                # 不继续遍历子节点,因为已经在 _extract_switch_branches 中处理

            else:
                # 继续遍历子节点
                for child in node.children:
                    traverse(child)

        traverse(method_body_node)
        self.branches.extend(branches)
        return branches

    def _extract_if_branches(self, if_node) -> List[BranchInfo]:
        """
        提取 if-else 链中的所有分支

        AST 结构:
        if_statement
          ├─ 'if' keyword
          ├─ condition (parenthesized_expression)
          ├─ consequence (block/statement)
          └─ alternative (if_statement 或 block) [可选]

        Args:
            if_node: if_statement 节点

        Returns:
            该 if-else 链的所有分支
        """
        branch_id = str(uuid.uuid4())
        branches = []
        current_node = if_node
        order = 1

        while current_node:
            if current_node.type != 'if_statement':
                # 这是最后的 else 块
                branches.append(BranchInfo(
                    branch_id=branch_id,
                    branch_type='else',
                    branch_order=order,
                    condition=None,
                    start_line=current_node.start_point[0] + 1,
                    end_line=current_node.end_point[0] + 1
                ))
                break

            # 提取条件表达式
            condition_node = None
            consequence_node = None
            alternative_node = None

            for i, child in enumerate(current_node.children):
                if child.type == 'parenthesized_expression':
                    condition_node = child
                elif child.type in ('block', 'expression_statement', 'return_statement',
                                   'method_invocation', 'local_variable_declaration'):
                    if consequence_node is None:
                        consequence_node = child
                    else:
                        alternative_node = child
                elif child.type == 'if_statement':
                    alternative_node = child

            # 提取条件文本 (去掉括号)
            condition_text = None
            if condition_node:
                condition_text = self._get_text(condition_node)
                # 去掉外层括号
                if condition_text.startswith('(') and condition_text.endswith(')'):
                    condition_text = condition_text[1:-1].strip()

            # 判断是 if 还是 else-if
            branch_type = 'if' if order == 1 else 'else-if'

            # 添加当前分支
            if consequence_node:
                branches.append(BranchInfo(
                    branch_id=branch_id,
                    branch_type=branch_type,
                    branch_order=order,
                    condition=condition_text,
                    start_line=consequence_node.start_point[0] + 1,
                    end_line=consequence_node.end_point[0] + 1
                ))

            # 继续处理 alternative
            order += 1
            current_node = alternative_node if alternative_node and alternative_node.type == 'if_statement' else None

            # 如果 alternative 不是 if_statement,说明是最后的 else 块
            if alternative_node and alternative_node.type != 'if_statement':
                branches.append(BranchInfo(
                    branch_id=branch_id,
                    branch_type='else',
                    branch_order=order,
                    condition=None,
                    start_line=alternative_node.start_point[0] + 1,
                    end_line=alternative_node.end_point[0] + 1
                ))
                break

        return branches

    def _extract_switch_branches(self, switch_node) -> List[BranchInfo]:
        """
        提取 switch 语句中的所有 case 分支

        AST 结构:
        switch_statement
          ├─ 'switch' keyword
          ├─ condition (parenthesized_expression)
          └─ switch_block
              ├─ switch_block_statement_group (case)
              ├─ switch_block_statement_group (case)
              └─ switch_block_statement_group (default) [可选]

        Args:
            switch_node: switch_statement 节点

        Returns:
            该 switch 的所有分支
        """
        branch_id = str(uuid.uuid4())
        branches = []
        order = 1

        # 查找 switch_block
        switch_block = None
        for child in switch_node.children:
            if child.type == 'switch_block':
                switch_block = child
                break

        if not switch_block:
            return branches

        # 遍历所有 case
        for child in switch_block.children:
            if child.type == 'switch_block_statement_group':
                # 查找 case 或 default 标签
                switch_label = None
                for label_child in child.children:
                    if label_child.type in ('switch_label', 'case', 'default'):
                        switch_label = label_child
                        break

                if switch_label:
                    # 提取 case 值或判断是否是 default
                    is_default = False
                    condition_text = None

                    for label_part in switch_label.children:
                        if label_part.type == 'default':
                            is_default = True
                        elif label_part.type != 'case' and label_part.type != ':':
                            # 这是 case 的值
                            condition_text = self._get_text(label_part)

                    branch_type = 'default' if is_default else 'case'

                    branches.append(BranchInfo(
                        branch_id=branch_id,
                        branch_type=branch_type,
                        branch_order=order,
                        condition=condition_text,
                        start_line=child.start_point[0] + 1,
                        end_line=child.end_point[0] + 1
                    ))
                    order += 1

        return branches

    def get_branch_at_line(self, line: int) -> Optional[BranchInfo]:
        """
        获取指定行所在的分支

        Args:
            line: 行号

        Returns:
            分支信息，如果不在分支内则返回 None
        """
        for branch in self.branches:
            if branch.start_line <= line <= branch.end_line:
                return branch
        return None

    def is_in_branch(self, line: int) -> bool:
        """
        判断某行是否在分支内

        Args:
            line: 行号

        Returns:
            True 如果在分支内，否则 False
        """
        return self.get_branch_at_line(line) is not None

    def _get_text(self, node) -> str:
        """获取节点文本"""
        if self.content_bytes and hasattr(node, 'start_byte'):
            return self.content_bytes[node.start_byte:node.end_byte].decode('utf-8')
        return ""

    def set_content_bytes(self, content_bytes: bytes):
        """设置内容字节（用于文本提取）"""
        self.content_bytes = content_bytes
