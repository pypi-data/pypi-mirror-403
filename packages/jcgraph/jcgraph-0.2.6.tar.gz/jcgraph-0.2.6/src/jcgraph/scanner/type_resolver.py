"""类型解析器 - 负责类型推断和泛型提取"""
from dataclasses import dataclass
from typing import Dict, Optional
import re

try:
    from tree_sitter import Language, Parser
    import tree_sitter_java as tsjava
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class TypeContext:
    """类型上下文 - 存储变量类型映射"""
    # 字段类型映射
    field_types: Dict[str, str]          # {字段名: 类型}
    field_generic_types: Dict[str, str]  # {字段名: 泛型参数类型}

    # 局部变量类型映射
    local_types: Dict[str, str]          # {变量名: 类型}

    # Lambda 参数类型映射
    lambda_param_types: Dict[str, str]   # {参数名: 类型}


class TypeResolver:
    """类型解析器"""

    def __init__(self, imports: Dict[str, str], current_package: str):
        """
        初始化类型解析器

        Args:
            imports: import语句映射 {"StringUtils": "com.ctrip.common.utils.StringUtils"}
            current_package: 当前包名
        """
        self.imports = imports
        self.current_package = current_package
        self.content_bytes = None

    def extract_field_types(self, fields: list) -> Dict[str, str]:
        """
        提取所有字段的类型

        Args:
            fields: FieldInfo 列表

        Returns:
            {字段名: 类型}
        """
        field_types = {}
        for field in fields:
            field_types[field.name] = field.type
        return field_types

    def extract_generic_type(self, type_str: str) -> Optional[str]:
        """
        从泛型类型中提取参数类型

        Examples:
            List<CardDomainBuilder> -> CardDomainBuilder
            Map<String, User> -> User (取 value 类型)
            Set<Integer> -> Integer

        Args:
            type_str: 泛型类型字符串

        Returns:
            泛型参数类型，如果无法提取则返回 None
        """
        # 匹配 List<Type>, Set<Type>, Collection<Type> 等
        match = re.match(r'(?:List|Set|Collection)<(.+)>', type_str)
        if match:
            return match.group(1)

        # 匹配 Map<K, V> - 提取 value 类型
        match = re.match(r'Map<[^,]+,\s*(.+)>', type_str)
        if match:
            return match.group(1)

        return None

    def extract_method_parameters(self, method_node) -> Dict[str, str]:
        """
        提取方法参数的类型

        Args:
            method_node: method_declaration AST 节点

        Returns:
            {参数名: 类型}
        """
        param_types = {}

        # 查找 formal_parameters 节点
        for child in method_node.children:
            if child.type == 'formal_parameters':
                # 遍历所有参数
                for param_child in child.children:
                    if param_child.type == 'formal_parameter':
                        # 提取类型和名称
                        type_node = param_child.child_by_field_name('type')
                        name_node = param_child.child_by_field_name('name')
                        if type_node and name_node:
                            param_type = self._get_text(type_node)
                            param_name = self._get_text(name_node)
                            param_types[param_name] = param_type

        return param_types

    def extract_local_variables(self, method_body_node) -> Dict[str, str]:
        """
        提取方法内局部变量的类型

        识别:
        1. local_variable_declaration: Type varName = ...;
        2. enhanced_for_statement: for (Type var : collection)
        3. resource_specification: try (Type var = ...)

        Args:
            method_body_node: 方法体 AST 节点

        Returns:
            {变量名: 类型}
        """
        local_vars = {}

        def traverse(node):
            # 普通局部变量声明
            if node.type == 'local_variable_declaration':
                type_node = node.child_by_field_name('type')
                if type_node:
                    type_name = self._get_text(type_node)
                    declarator_nodes = [n for n in node.children if n.type == 'variable_declarator']
                    for decl in declarator_nodes:
                        name_node = decl.child_by_field_name('name')
                        if name_node:
                            var_name = self._get_text(name_node)
                            local_vars[var_name] = type_name

            # 增强for循环
            elif node.type == 'enhanced_for_statement':
                type_node = node.children[1] if len(node.children) > 1 else None
                name_node = node.children[2] if len(node.children) > 2 else None
                if type_node and name_node and type_node.type != 'identifier':
                    var_name = self._get_text(name_node)
                    type_name = self._get_text(type_node)
                    local_vars[var_name] = type_name

            for child in node.children:
                traverse(child)

        traverse(method_body_node)
        return local_vars

    def infer_lambda_param_type(self,
                                 collection_var: str,
                                 lambda_param: str,
                                 field_types: Dict[str, str],
                                 local_types: Dict[str, str]) -> Optional[str]:
        """
        推断 Lambda 参数类型

        collection.stream().filter(x -> ...)
        x 的类型 = collection 的泛型参数

        Args:
            collection_var: 集合变量名
            lambda_param: lambda 参数名
            field_types: 字段类型映射
            local_types: 局部变量类型映射

        Returns:
            推断出的类型，如果无法推断则返回 None
        """
        # 先查找变量的类型
        var_type = None
        if collection_var in local_types:
            var_type = local_types[collection_var]
        elif collection_var in field_types:
            var_type = field_types[collection_var]

        if not var_type:
            return None

        # 提取泛型参数
        return self.extract_generic_type(var_type)

    def resolve_type(self, type_name: str) -> Optional[str]:
        """
        解析类型名称到完整类名

        Args:
            type_name: 类型名称（可能是简称或完整名）

        Returns:
            完整类名，如果无法解析则返回 None
        """
        # 已经是完整名称
        if '.' in type_name:
            return type_name

        # 查找 imports
        if type_name in self.imports:
            return self.imports[type_name]

        # 尝试同包类
        if self.current_package:
            return f"{self.current_package}.{type_name}"

        return None

    def _get_text(self, node) -> str:
        """获取节点文本"""
        if self.content_bytes and hasattr(node, 'start_byte'):
            return self.content_bytes[node.start_byte:node.end_byte].decode('utf-8')
        return ""

    def set_content_bytes(self, content_bytes: bytes):
        """设置内容字节（用于文本提取）"""
        self.content_bytes = content_bytes
