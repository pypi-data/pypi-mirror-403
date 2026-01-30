"""Java代码解析器"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union, List, Dict

try:
    from tree_sitter import Language, Parser
    import tree_sitter_java as tsjava
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class ClassInfo:
    """类信息"""
    name: str                    # 类名
    package: str                 # 包名
    full_name: str               # 完整类名 com.ctrip.OrderService
    type: str                    # class/interface/enum/abstract
    annotations: List[str] = field(default_factory=list)  # 注解列表
    comment: Optional[str] = None          # 类注释
    extends: Optional[str] = None          # 父类
    implements: List[str] = field(default_factory=list)  # 实现的接口
    file_path: str = ""          # 文件路径
    line_start: int = 0
    line_end: int = 0


@dataclass
class MethodInfo:
    """方法信息"""
    name: str                    # 方法名
    class_name: str              # 所属类
    full_name: str               # 完整方法名 com.ctrip.OrderService#query
    signature: str               # 方法签名 query(Long orderId)
    params: List[Dict] = field(default_factory=list)  # 参数
    return_type: str = "void"    # 返回类型
    visibility: str = "public"   # public/private/protected
    annotations: List[str] = field(default_factory=list)  # 注解
    comment: Optional[str] = None          # 方法注释
    code: str = ""               # 方法体代码
    line_start: int = 0
    line_end: int = 0
    subtype: str = "normal"      # normal/abstract/static


@dataclass
class FieldInfo:
    """字段信息"""
    name: str                    # 字段名
    class_name: str              # 所属类
    type: str                    # 类型
    annotations: List[str] = field(default_factory=list)  # 注解
    visibility: str = "private"


@dataclass
class ParseResult:
    """解析结果"""
    file_path: str
    package: str = ""
    imports: Dict[str, str] = field(default_factory=dict)  # {"StringUtils": "com.ctrip.common.utils.StringUtils"}
    classes: List[ClassInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    fields: List[FieldInfo] = field(default_factory=list)


class JavaParser:
    """Java解析器"""

    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter 未安装。请运行: pip install tree-sitter tree-sitter-java"
            )

        # 初始化解析器
        self.parser = Parser()
        self.parser.language = Language(tsjava.language())

    def parse_file(self, file_path: Union[Path, str]) -> ParseResult:
        """解析Java文件"""
        file_path = Path(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_content(content, str(file_path))

    def parse_content(self, content: str, file_path: str = "") -> ParseResult:
        """解析Java代码内容"""
        # 保存原始内容和字节内容用于文本提取
        self.content_str = content
        self.content_bytes = bytes(content, 'utf8')

        tree = self.parser.parse(self.content_bytes)
        root = tree.root_node

        result = ParseResult(file_path=file_path)

        # 提取包名
        result.package = self._extract_package(root, content)

        # 提取import语句
        result.imports = self._extract_imports(root, content)

        # 提取类信息
        for class_node in self._find_nodes(root, [
            'class_declaration',
            'interface_declaration',
            'enum_declaration'
        ]):
            class_info = self._extract_class(class_node, content, result.package, file_path)
            result.classes.append(class_info)

            # 提取方法
            for method_node in self._find_nodes(class_node, ['method_declaration']):
                method_info = self._extract_method(
                    method_node, content, class_info.full_name
                )
                # 接口中的方法默认是abstract的（除非有default修饰符）
                if class_info.type == 'interface' and method_info.subtype == 'normal':
                    method_info.subtype = 'abstract'
                result.methods.append(method_info)

            # 提取字段
            for field_node in self._find_nodes(class_node, ['field_declaration']):
                field_info = self._extract_field(field_node, content, class_info.name)
                result.fields.append(field_info)

            # 为 Lombok 注解生成虚拟的 getter/setter 方法
            lombok_methods = self._generate_lombok_methods(class_info, result.fields, file_path)
            # if lombok_methods:
            #     print(f"[DEBUG] 为类 {class_info.name} 生成了 {len(lombok_methods)} 个 Lombok 方法")
            result.methods.extend(lombok_methods)

        return result

    def _extract_package(self, root, content: str) -> str:
        """提取包名"""
        for child in root.children:
            if child.type == 'package_declaration':
                # 获取包名节点
                for node in child.children:
                    if node.type == 'scoped_identifier' or node.type == 'identifier':
                        return self._get_text(node, content)
        return ""

    def _extract_imports(self, root, content: str) -> Dict[str, str]:
        """
        提取import语句
        返回: {"StringUtils": "com.ctrip.common.utils.StringUtils", "*": "com.ctrip.xxx.*"}
        """
        imports = {}

        for child in root.children:
            if child.type == 'import_declaration':
                import_path = None

                # 查找导入路径（scoped_identifier或identifier）
                for node in child.children:
                    if node.type in ['scoped_identifier', 'identifier']:
                        import_path = self._get_text(node, content)
                        break
                    # 处理 import xxx.*;
                    elif node.type == 'asterisk':
                        if import_path:
                            imports['*'] = import_path + '.*'
                        break

                if import_path:
                    # 提取简单类名
                    if '.' in import_path:
                        simple_name = import_path.split('.')[-1]
                        imports[simple_name] = import_path
                    else:
                        imports[import_path] = import_path

        return imports

    def _extract_class(self, node, content: str, package: str, file_path: str) -> ClassInfo:
        """提取类信息"""
        class_name = ""
        class_type = "class"
        annotations = []
        comment = None
        extends = None
        implements = []

        # 获取类型
        if node.type == 'interface_declaration':
            class_type = "interface"
        elif node.type == 'enum_declaration':
            class_type = "enum"

        # 获取类名 - 查找class/interface/enum关键字后的第一个identifier
        found_keyword = False
        for child in node.children:
            if child.type in ['class', 'interface', 'enum']:
                found_keyword = True
            elif found_keyword and child.type == 'identifier':
                class_name = self._get_text(child, content)
                break

        # 获取父类和接口
        for child in node.children:
            if child.type == 'superclass':
                extends = self._get_text(child, content).replace('extends', '').strip()
            elif child.type == 'super_interfaces':
                impl_text = self._get_text(child, content).replace('implements', '').strip()
                implements = [i.strip() for i in impl_text.split(',')]

        # 获取注解（从modifiers中提取）
        modifiers_node = self._find_child(node, 'modifiers')
        if modifiers_node:
            annotations = self._extract_annotations(modifiers_node, content)

        # 生成完整类名
        full_name = f"{package}.{class_name}" if package else class_name

        return ClassInfo(
            name=class_name,
            package=package,
            full_name=full_name,
            type=class_type,
            annotations=annotations,
            comment=comment,
            extends=extends,
            implements=implements,
            file_path=file_path,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1
        )

    def _extract_method(self, node, content: str, class_full_name: str) -> MethodInfo:
        """提取方法信息"""
        method_name = ""
        params = []
        return_type = "void"
        visibility = "public"
        annotations = []
        code = self._get_text(node, content)

        # 获取方法名
        for child in node.children:
            if child.type == 'identifier':
                method_name = self._get_text(child, content)
                break

        # 获取返回类型
        for child in node.children:
            if child.type in ['type_identifier', 'void_type', 'integral_type', 'generic_type']:
                return_type = self._get_text(child, content)
                break

        # 获取参数
        formal_params = self._find_child(node, 'formal_parameters')
        if formal_params:
            params = self._extract_params(formal_params, content)

        # 获取可见性、注解和修饰符
        modifiers_node = self._find_child(node, 'modifiers')
        method_modifiers = []
        if modifiers_node:
            visibility = self._extract_visibility(modifiers_node, content)
            annotations = self._extract_annotations(modifiers_node, content)
            method_modifiers = self._extract_modifiers(modifiers_node, content)

        # 确定方法 subtype
        subtype = "normal"
        if 'abstract' in method_modifiers:
            subtype = "abstract"
        elif 'static' in method_modifiers:
            subtype = "static"

        # 生成签名
        param_str = ', '.join(f"{p['type']} {p['name']}" for p in params)
        signature = f"{method_name}({param_str})"
        full_name = f"{class_full_name}#{method_name}"

        return MethodInfo(
            name=method_name,
            class_name=class_full_name,
            full_name=full_name,
            signature=signature,
            params=params,
            return_type=return_type,
            visibility=visibility,
            annotations=annotations,
            code=code,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            subtype=subtype
        )

    def _extract_field(self, node, content: str, class_name: str) -> FieldInfo:
        """提取字段信息"""
        field_name = ""
        field_type = ""
        visibility = "private"
        annotations = []

        # 获取字段类型
        for child in node.children:
            if child.type in ['type_identifier', 'integral_type', 'generic_type']:
                field_type = self._get_text(child, content)
                break

        # 获取字段名
        declarator = self._find_child(node, 'variable_declarator')
        if declarator:
            for child in declarator.children:
                if child.type == 'identifier':
                    field_name = self._get_text(child, content)
                    break

        # 获取可见性和注解
        modifiers_node = self._find_child(node, 'modifiers')
        if modifiers_node:
            visibility = self._extract_visibility(modifiers_node, content)
            annotations = self._extract_annotations(modifiers_node, content)

        return FieldInfo(
            name=field_name,
            class_name=class_name,
            type=field_type,
            annotations=annotations,
            visibility=visibility
        )

    def _extract_params(self, node, content: str) -> List[Dict]:
        """提取方法参数"""
        params = []
        for child in node.children:
            if child.type == 'formal_parameter':
                param_type = ""
                param_name = ""

                for param_child in child.children:
                    if param_child.type in ['type_identifier', 'integral_type', 'generic_type']:
                        param_type = self._get_text(param_child, content)
                    elif param_child.type == 'identifier':
                        param_name = self._get_text(param_child, content)

                if param_name:
                    params.append({"name": param_name, "type": param_type})

        return params

    def _extract_visibility(self, modifiers_node, content: str) -> str:
        """提取可见性"""
        text = self._get_text(modifiers_node, content)
        if 'public' in text:
            return 'public'
        elif 'private' in text:
            return 'private'
        elif 'protected' in text:
            return 'protected'
        return 'package'

    def _extract_modifiers(self, modifiers_node, content: str) -> List[str]:
        """提取所有修饰符"""
        modifiers = []
        for child in modifiers_node.children:
            if child.type in ['public', 'private', 'protected', 'static', 'final', 'abstract', 'synchronized', 'native', 'strictfp']:
                modifiers.append(child.type)
        return modifiers

    def _extract_annotations(self, modifiers_node, content: str) -> List[str]:
        """提取注解"""
        annotations = []
        for child in modifiers_node.children:
            if child.type == 'marker_annotation' or child.type == 'annotation':
                anno_text = self._get_text(child, content)
                annotations.append(anno_text)
        return annotations

    def _generate_lombok_methods(self, class_info: ClassInfo, fields: List[FieldInfo], file_path: str) -> List[MethodInfo]:
        """为 Lombok 注解生成虚拟的 getter/setter 方法"""
        lombok_methods = []

        # 检查类级别的 Lombok 注解
        has_data = any('@Data' in anno for anno in class_info.annotations)
        has_getter = any('@Getter' in anno for anno in class_info.annotations)
        has_setter = any('@Setter' in anno for anno in class_info.annotations)

        if not (has_data or has_getter or has_setter):
            return lombok_methods

        # 为每个字段生成 getter/setter
        for field in fields:
            if field.class_name != class_info.name:
                continue

            field_name = field.name
            field_type = field.type

            # 生成 getter 方法名
            # 布尔类型: isXxx / getXxx
            # 其他类型: getXxx
            if field_type == 'boolean' or field_type == 'Boolean':
                getter_name = f"is{field_name[0].upper()}{field_name[1:]}"
            else:
                getter_name = f"get{field_name[0].upper()}{field_name[1:]}"

            # 生成 setter 方法名
            setter_name = f"set{field_name[0].upper()}{field_name[1:]}"

            # 创建 getter 方法
            if has_data or has_getter:
                getter = MethodInfo(
                    name=getter_name,
                    full_name=f"{class_info.full_name}#{getter_name}",
                    class_name=class_info.full_name,
                    signature=f"{getter_name}()",
                    return_type=field_type,
                    params=[],
                    line_start=0,  # Lombok 生成的方法没有行号
                    line_end=0,
                    annotations=['@Lombok-Generated'],
                    subtype='lombok-getter'
                )
                lombok_methods.append(getter)

            # 创建 setter 方法
            if has_data or has_setter:
                setter = MethodInfo(
                    name=setter_name,
                    full_name=f"{class_info.full_name}#{setter_name}",
                    class_name=class_info.full_name,
                    signature=f"{setter_name}({field_type} {field_name})",
                    return_type='void',
                    params=[{'type': field_type, 'name': field_name}],
                    line_start=0,
                    line_end=0,
                    annotations=['@Lombok-Generated'],
                    subtype='lombok-setter'
                )
                lombok_methods.append(setter)

        return lombok_methods

    def _find_nodes(self, root, node_types: List[str]):
        """递归查找指定类型的节点"""
        def traverse(node):
            if node.type in node_types:
                yield node
            for child in node.children:
                yield from traverse(child)

        return traverse(root)

    def _find_child(self, node, child_type: str):
        """查找直接子节点"""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def _get_text(self, node, content: str) -> str:
        """获取节点文本 - 使用字节偏移正确提取"""
        return self.content_bytes[node.start_byte:node.end_byte].decode('utf8')


# 便捷函数
def parse_file(file_path: Union[Path, str]) -> ParseResult:
    """解析Java文件"""
    parser = JavaParser()
    return parser.parse_file(file_path)


def parse_content(content: str, file_path: str = "") -> ParseResult:
    """解析Java代码内容"""
    parser = JavaParser()
    return parser.parse_content(content, file_path)
