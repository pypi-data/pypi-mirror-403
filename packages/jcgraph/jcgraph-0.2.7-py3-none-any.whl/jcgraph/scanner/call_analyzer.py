"""调用分析器 - 负责分析方法调用"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import uuid

from jcgraph.scanner.loop_detector import STREAM_LOOP_METHODS, LOOP_NODE_TYPES
from jcgraph.scanner.branch_detector import BranchDetector, BRANCH_NODE_TYPES


@dataclass
class CallInfo:
    """调用信息"""
    line: int
    caller: str              # 调用者 (如 b, this, ClassName)
    caller_type: str         # 调用者的类型
    method_name: str         # 方法名
    raw: str                 # 原始文本 (如 b.need(context))

    # 目标信息
    target_id: Optional[str] = None  # 被调用方法的完整ID
    target_type: str = ""            # 目标类型

    # 循环相关
    loop_type: Optional[str] = None
    loop_id: Optional[str] = None
    lambda_depth: int = 0            # Lambda 嵌套深度

    # 分支相关
    branch_type: Optional[str] = None      # 'if', 'else-if', 'else', 'case', 'default'
    branch_id: Optional[str] = None        # 分支组ID
    branch_condition: Optional[str] = None # 条件表达式
    branch_order: int = 0                  # 分支顺序

    # 接口相关
    is_interface_call: bool = False


class CallAnalyzer:
    """调用分析器"""

    def __init__(self,
                 source_method_id: str,
                 imports: Dict[str, str],
                 current_package: str,
                 field_types: Dict[str, str],
                 local_types: Dict[str, str],
                 known_interfaces: Set[str],
                 type_resolver):
        """
        初始化调用分析器

        Args:
            source_method_id: 源方法ID
            imports: import映射
            current_package: 当前包名
            field_types: 字段类型映射
            local_types: 局部变量类型映射
            known_interfaces: 已知接口集合
            type_resolver: 类型解析器
        """
        self.source_method_id = source_method_id
        self.imports = imports
        self.current_package = current_package
        self.field_types = field_types
        self.local_types = local_types
        self.known_interfaces = known_interfaces
        self.type_resolver = type_resolver
        self.content_bytes = None

    def analyze(self, method_body_node) -> List[CallInfo]:
        """
        分析所有方法调用

        Args:
            method_body_node: 方法体 AST 节点

        Returns:
            调用信息列表
        """
        calls = []

        # 临时保存原始 local_types
        original_local_types = self.local_types

        # 先检测所有分支
        branch_detector = BranchDetector()
        branch_detector.set_content_bytes(self.content_bytes)
        all_branches = branch_detector.detect_branches(method_body_node)

        # 创建行号到分支的映射
        line_to_branch = {}
        for branch in all_branches:
            for line in range(branch.start_line, branch.end_line + 1):
                line_to_branch[line] = branch

        def traverse(node, loop_context=None, branch_context=None):
            """遍历 AST 节点提取调用"""
            # 检查是否是分支节点 (if/switch) - 分支不需要传递上下文,因为我们用行号映射
            if node.type in BRANCH_NODE_TYPES:
                # 分支由 line_to_branch 映射处理,不需要上下文传递
                # 继续遍历子节点即可
                for child in node.children:
                    traverse(child, loop_context, branch_context)
                return

            # 检查是否是传统循环节点 (for/foreach/while)
            if node.type in LOOP_NODE_TYPES:
                # 创建新的循环上下文
                new_loop_context = {
                    'loop_type': LOOP_NODE_TYPES[node.type],
                    'loop_id': str(uuid.uuid4()),
                    'lambda_depth': loop_context['lambda_depth'] if loop_context else 0
                }

                # 如果是 enhanced_for (foreach) 循环，提取循环变量类型
                if node.type == 'enhanced_for_statement':
                    loop_var_types = self._extract_foreach_var_type(node)
                    if loop_var_types:
                        # 临时扩展 local_types
                        self.local_types = {**self.local_types, **loop_var_types}

                        # 递归处理循环体
                        for child in node.children:
                            traverse(child, new_loop_context)

                        # 恢复原始 local_types
                        self.local_types = original_local_types
                        return

                # 其他循环类型（for/while）正常处理
                for child in node.children:
                    traverse(child, new_loop_context)
                return

            # 检查方法调用
            if node.type == 'method_invocation':
                call_info = self._parse_method_invocation(node)
                if call_info:
                    # 应用循环上下文
                    if loop_context:
                        call_info.loop_type = loop_context['loop_type']
                        call_info.loop_id = loop_context['loop_id']
                        call_info.lambda_depth = loop_context['lambda_depth']

                    # 应用分支上下文
                    if call_info.line in line_to_branch:
                        branch = line_to_branch[call_info.line]
                        call_info.branch_type = branch.branch_type
                        call_info.branch_id = branch.branch_id
                        call_info.branch_condition = branch.condition
                        call_info.branch_order = branch.branch_order

                    # 检查是否是 stream 方法 - 需要为 lambda 创建循环上下文
                    if call_info.method_name in STREAM_LOOP_METHODS:
                        # 这是一个 stream 循环方法，为它创建循环上下文
                        stream_loop_context = {
                            'loop_type': 'stream',
                            'loop_id': str(uuid.uuid4()),
                            'lambda_depth': 0
                        }
                        call_info.loop_type = 'stream'
                        call_info.loop_id = stream_loop_context['loop_id']

                        # 查找此方法调用的参数中的 lambda 表达式
                        for child in node.children:
                            if child.type == 'argument_list':
                                for arg in child.children:
                                    if arg.type == 'lambda_expression':
                                        # 提取 lambda 参数并推断类型
                                        lambda_param_types = self._infer_lambda_param_types(node, arg)

                                        # 临时扩展 local_types 以包含 lambda 参数
                                        self.local_types = {**self.local_types, **lambda_param_types}

                                        # 在 lambda 内部应用循环上下文
                                        lambda_context = {
                                            'loop_type': 'stream',
                                            'loop_id': stream_loop_context['loop_id'],
                                            'lambda_depth': 1
                                        }
                                        for lambda_child in arg.children:
                                            traverse(lambda_child, lambda_context)

                                        # 恢复原始 local_types
                                        self.local_types = original_local_types

                                        # 跳过后续对此 lambda 的处理
                                        continue

                    calls.append(call_info)

            # 继续遍历子节点
            for child in node.children:
                # 跳过已处理的 lambda
                if child.type == 'argument_list':
                    for arg in child.children:
                        if arg.type != 'lambda_expression':
                            traverse(arg, loop_context)
                elif child.type != 'argument_list':
                    traverse(child, loop_context)

        traverse(method_body_node)
        return calls

    def _parse_method_invocation(self, node) -> Optional[CallInfo]:
        """
        解析单个方法调用

        处理：
        1. fieldName.methodName() -> 查找字段类型
        2. localVar.methodName() -> 查找局部变量类型
        3. ClassName.staticMethod() -> 静态方法（首字母大写）
        4. this.methodName() -> 同类方法
        5. methodName() -> 同类方法

        Args:
            node: method_invocation 节点

        Returns:
            CallInfo 或 None
        """
        call_text = self._get_text(node)
        line_number = node.start_point[0] + 1

        # 提取对象和方法名
        object_node = None
        method_name_node = None

        identifiers = [child for child in node.children if child.type == 'identifier']

        # 检查是否有 field_access（字段调用）
        has_field_access = False
        for child in node.children:
            if child.type == 'field_access':
                has_field_access = True
                # object.methodName 形式
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        object_node = subchild
                        break

        if has_field_access and len(identifiers) > 0:
            # field_access + identifier: obj.method()
            method_name_node = identifiers[0]
        elif len(identifiers) == 2:
            # 两个 identifier: ClassName.method() (静态调用)
            object_node = identifiers[0]
            method_name_node = identifiers[1]
        elif len(identifiers) == 1:
            # 单个 identifier: method() (同类调用)
            method_name_node = identifiers[0]

        if not method_name_node:
            return None

        method_name = self._get_text(method_name_node)
        caller = ""
        caller_type = ""

        # 确定目标类型
        target_type = None
        if object_node:
            object_name = self._get_text(object_node)
            caller = object_name


            # 1. 判断是否是静态调用（首字母大写）
            if object_name and object_name[0].isupper():
                # 可能是静态调用：ClassName.method()
                # 从 imports 查找完整类名
                if object_name in self.imports:
                    target_type = self.imports[object_name]
                else:
                    # 尝试同包类
                    target_type = object_name
                caller_type = target_type if target_type else object_name
            # 2. 查找局部变量类型
            elif object_name in self.local_types:
                target_type = self.local_types[object_name]
                caller_type = target_type
            # 3. 查找字段类型
            elif object_name in self.field_types:
                target_type = self.field_types[object_name]
                caller_type = target_type
        else:
            # 没有对象 -> 同类方法或 this.method()
            caller = "this"
            target_type = self.source_method_id.split('#')[0]  # 提取类名
            caller_type = target_type

        # 解析目标完整方法ID
        target_id = None
        if target_type:
            # 已经是完整类名（包含 .）
            if '.' in target_type:
                target_full_type = target_type
            # 优先使用 imports 解析
            elif target_type in self.imports:
                target_full_type = self.imports[target_type]
            else:
                target_full_type = self.type_resolver.resolve_type(target_type)

            if target_full_type:
                target_id = f"{target_full_type}#{method_name}"
                target_type = target_full_type

        # 检查是否是接口调用
        is_interface_call = target_type in self.known_interfaces if target_type else False

        return CallInfo(
            line=line_number,
            caller=caller,
            caller_type=caller_type,
            method_name=method_name,
            raw=call_text,
            target_id=target_id,
            target_type=target_type,
            is_interface_call=is_interface_call
        )

    def _get_text(self, node) -> str:
        """获取节点文本"""
        if self.content_bytes and hasattr(node, 'start_byte'):
            return self.content_bytes[node.start_byte:node.end_byte].decode('utf-8')
        return ""

    def set_content_bytes(self, content_bytes: bytes):
        """设置内容字节（用于文本提取）"""
        self.content_bytes = content_bytes

    def _infer_lambda_param_types(self, stream_method_node, lambda_node) -> Dict[str, str]:
        """
        推断 Lambda 参数的类型

        例如: users.stream().filter(user -> ...)
        - stream_method_node: filter 方法调用节点
        - lambda_node: lambda 表达式节点
        - 返回: {"user": "User"}

        Args:
            stream_method_node: stream 方法调用节点 (如 filter, map)
            lambda_node: lambda 表达式节点

        Returns:
            {参数名: 类型} 字典
        """
        lambda_param_types = {}

        # 1. 提取 lambda 参数名
        # lambda_expression 结构: (param) -> body 或 param -> body
        lambda_params = []
        for child in lambda_node.children:
            if child.type == 'identifier':
                # 单参数形式: user -> ...
                lambda_params.append(self._get_text(child))
                break
            elif child.type == 'inferred_parameters':
                # 多参数形式: (a, b) -> ...
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        lambda_params.append(self._get_text(subchild))

        if not lambda_params:
            return {}

        # 2. 找到 stream() 调用的对象
        # 向上回溯找到 .stream() 之前的对象
        # 例如: users.stream().filter(...) 中找到 users
        collection_var = self._extract_collection_var(stream_method_node)

        if not collection_var:
            return {}

        # 3. 查找集合的类型
        collection_type = None
        if collection_var in self.local_types:
            collection_type = self.local_types[collection_var]
        elif collection_var in self.field_types:
            collection_type = self.field_types[collection_var]

        if not collection_type:
            return {}

        # 4. 提取泛型参数
        generic_type = self.type_resolver.extract_generic_type(collection_type)
        if generic_type:
            # 解析泛型类型为完整类名
            full_generic_type = self.type_resolver.resolve_type(generic_type)
            if full_generic_type:
                # 将完整类型分配给第一个 lambda 参数
                lambda_param_types[lambda_params[0]] = full_generic_type
            else:
                # 如果无法解析，使用简单类名
                lambda_param_types[lambda_params[0]] = generic_type

        return lambda_param_types

    def _extract_collection_var(self, node) -> Optional[str]:
        """
        从 stream 方法调用中提取集合变量名

        例如: users.stream().filter(...) -> "users"

        Args:
            node: method_invocation 节点

        Returns:
            集合变量名或 None
        """
        # 查找 field_access 节点，它包含调用链
        # users.stream().filter() 的结构:
        # method_invocation(filter)
        #   field_access
        #     method_invocation(stream)
        #       field_access
        #         identifier(users)

        # tree-sitter Java 的 AST 结构:
        # users.stream().filter(...) 实际结构是:
        # method_invocation (filter)
        #   method_invocation (stream)
        #     field_access
        #       identifier (users)
        #     .
        #     identifier (stream)
        #   .
        #   identifier (filter)
        #   argument_list

        # 先查找子节点中的 method_invocation (chain的前一个方法)
        for child in node.children:
            if child.type == 'method_invocation':
                # 递归查找最深层的 identifier
                result = self._find_deepest_identifier(child)
                if result:
                    return result

        # 如果没有找到 method_invocation，尝试直接查找 field_access 或 identifier
        # 这处理 list.forEach() 这种直接调用的情况
        for child in node.children:
            if child.type == 'field_access':
                result = self._find_deepest_identifier(child)
                if result:
                    return result
            elif child.type == 'identifier':
                # 第一个 identifier 可能是集合变量
                # 但要排除方法名本身（forEach, map 等）
                text = self._get_text(child)
                if text not in STREAM_LOOP_METHODS:
                    return text

        return None

    def _find_deepest_identifier(self, node) -> Optional[str]:
        """
        递归查找最深层的 identifier（集合变量）

        Args:
            node: AST 节点

        Returns:
            变量名或 None
        """
        # 先在子节点中查找
        for child in node.children:
            if child.type == 'method_invocation':
                # 继续向下查找
                result = self._find_deepest_identifier(child)
                if result:
                    return result
            elif child.type == 'field_access':
                # 继续向下查找
                result = self._find_deepest_identifier(child)
                if result:
                    return result
            elif child.type == 'identifier':
                # 找到了最深层的 identifier
                return self._get_text(child)

        return None

    def _extract_foreach_var_type(self, foreach_node) -> Dict[str, str]:
        """
        从 enhanced_for_statement 中提取循环变量及其类型

        例如: for (DataProcessor p : processors) { ... }
        返回: {"p": "com.example.demo.DataProcessor"}

        AST 结构:
        enhanced_for_statement
          type_identifier (DataProcessor)
          identifier (p)
          identifier (processors)
          block

        Args:
            foreach_node: enhanced_for_statement 节点

        Returns:
            {变量名: 类型} 字典
        """
        var_types = {}

        # 提取循环变量名和类型
        var_name = None
        var_type = None

        children = list(foreach_node.children)
        for i, child in enumerate(children):
            # 查找类型节点（type_identifier 或 generic_type）
            if child.type in ('type_identifier', 'generic_type'):
                var_type = self._get_text(child)
            # 查找变量名（identifier，但要排除集合变量）
            elif child.type == 'identifier':
                if var_name is None:
                    # 第一个 identifier 是循环变量
                    var_name = self._get_text(child)

        if not var_name or not var_type:
            return {}

        # 解析类型为完整类名
        full_type = self.type_resolver.resolve_type(var_type)
        if full_type:
            var_types[var_name] = full_type
        else:
            # 如果无法解析，使用简单类名
            var_types[var_name] = var_type

        return var_types
