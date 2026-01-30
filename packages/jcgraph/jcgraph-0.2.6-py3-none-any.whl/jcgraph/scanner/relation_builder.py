"""关系构建器 - 协调各模块，组装最终关系"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import re

from jcgraph.scanner.java_parser import ClassInfo, MethodInfo, FieldInfo
from jcgraph.scanner.type_resolver import TypeResolver
from jcgraph.scanner.loop_detector import LoopDetector
from jcgraph.scanner.call_analyzer import CallAnalyzer, CallInfo
from jcgraph.storage.sqlite import Storage

try:
    from tree_sitter import Language, Parser
    import tree_sitter_java as tsjava
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class Relation:
    """关系"""
    source_id: str          # 调用方 node_id
    target_id: Optional[str]  # 被调用方 node_id (可能未解析)
    target_raw: str         # 原始调用文本
    relation_type: str      # CALLS/IMPLEMENTS/EXTENDS/INJECTS/VIRTUAL_CALL
    line_number: int = 0    # 调用行号
    resolved: bool = False  # 是否解析到具体node
    loop_type: Optional[str] = None      # 循环类型: for/foreach/while/stream
    loop_id: Optional[str] = None        # 循环ID
    is_interface_call: int = 0           # 是否是接口调用
    lambda_depth: int = 0                # Lambda嵌套深度
    # 分支相关
    branch_type: Optional[str] = None    # 分支类型: if/else-if/else/case/default
    branch_id: Optional[str] = None      # 分支组ID
    branch_condition: Optional[str] = None  # 条件表达式
    branch_order: int = 0                # 分支顺序
    # 虚拟调用相关
    is_virtual: int = 0                  # 是否是虚拟调用边
    actual_target_id: Optional[str] = None  # 虚拟调用的实际目标（实现类方法）
    via_interface_id: Optional[str] = None  # 通过哪个接口调用


class RelationBuilder:
    """关系构建器 - 协调各模块"""

    def __init__(self, storage: Storage, project_id: str):
        """
        初始化关系构建器

        Args:
            storage: 数据库存储
            project_id: 项目ID
        """
        self.storage = storage
        self.project_id = project_id
        self.symbol_table: Dict[str, str] = {}
        self.known_interfaces: Set[str] = set()

        # 添加 tree-sitter parser 初始化
        if TREE_SITTER_AVAILABLE:
            self.parser = Parser()
            self.parser.language = Language(tsjava.language())
        else:
            self.parser = None

    def build_symbol_table(self) -> None:
        """构建符号表：简称 → 完整类名"""
        # 获取所有类节点
        classes = self.storage.list_nodes(
            self.project_id,
            node_type="class",
            limit=10000
        )
        classes += self.storage.list_nodes(
            self.project_id,
            node_type="interface",
            limit=10000
        )
        classes += self.storage.list_nodes(
            self.project_id,
            node_type="enum",
            limit=10000
        )

        # 建立映射并识别接口
        for cls in classes:
            simple_name = cls['name']
            full_name = cls['full_name']
            # 简单名称映射
            self.symbol_table[simple_name] = full_name
            # 完整名称也存储
            self.symbol_table[full_name] = full_name

            # 记录接口
            if cls.get('type') == 'interface' or cls.get('subtype') == 'abstract':
                self.known_interfaces.add(full_name)

    def analyze_class_relations(self, class_info: ClassInfo) -> List[Relation]:
        """
        分析类的继承和实现关系

        Args:
            class_info: 类信息

        Returns:
            关系列表
        """
        relations = []

        # EXTENDS - 继承关系
        if class_info.extends:
            # 尝试解析父类的完整名称
            parent_full_name = self._resolve_type(
                class_info.extends,
                class_info.package
            )

            relations.append(Relation(
                source_id=class_info.full_name,
                target_id=parent_full_name if parent_full_name in self.symbol_table.values() else None,
                target_raw=class_info.extends,
                relation_type="EXTENDS",
                resolved=parent_full_name is not None
            ))

        # IMPLEMENTS - 实现接口
        for interface in class_info.implements:
            interface_full_name = self._resolve_type(interface, class_info.package)

            relations.append(Relation(
                source_id=class_info.full_name,
                target_id=interface_full_name if interface_full_name in self.symbol_table.values() else None,
                target_raw=interface,
                relation_type="IMPLEMENTS",
                resolved=interface_full_name is not None
            ))

        return relations

    def analyze_override_relations(
        self,
        class_info: ClassInfo,
        methods: List[MethodInfo]
    ) -> List[Relation]:
        """
        分析方法覆写关系

        识别条件：
        1. 方法有 @Override 注解
        2. 父类/接口中存在同名方法

        生成：
        source_id: 子类方法 (CardDetailTemplate#buildDos)
        target_id: 父类方法 (ProductDetailTemplate#buildDos)
        relation_type: 'OVERRIDES'
        branch_label: 从类名提取 (CARD)
        """
        relations = []

        for method in methods:
            # 检查是否有 @Override 注解
            has_override = any('@Override' in anno for anno in method.annotations)

            if not has_override:
                continue

            # 查找父类/接口中的同名方法
            parent_method_id = self._find_parent_method(
                class_info,
                method.name
            )

            if parent_method_id:
                relations.append(Relation(
                    source_id=method.full_name,
                    target_id=parent_method_id,
                    target_raw=f"@Override {method.name}",
                    relation_type='OVERRIDES',
                    line_number=method.line_start,
                    resolved=True
                ))

        return relations

    def _find_parent_method(
        self,
        class_info: ClassInfo,
        method_name: str
    ) -> Optional[str]:
        """
        在父类/接口中查找同名方法

        查找顺序：
        1. extends 的父类
        2. implements 的接口
        """
        # 查父类
        if class_info.extends:
            parent_full_name = self._resolve_type(class_info.extends, class_info.package)
            if parent_full_name:
                parent_method_id = f"{parent_full_name}#{method_name}"
                # 检查方法是否存在于数据库
                if self._method_exists(parent_method_id):
                    return parent_method_id

        # 查接口
        for interface in class_info.implements:
            interface_full_name = self._resolve_type(interface, class_info.package)
            if interface_full_name:
                interface_method_id = f"{interface_full_name}#{method_name}"
                if self._method_exists(interface_method_id):
                    return interface_method_id

        return None

    def _method_exists(self, method_id: str) -> bool:
        """检查方法是否存在于数据库"""
        cursor = self.storage.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM nodes WHERE id = ? AND type = 'method' LIMIT 1",
            (method_id,)
        )
        return cursor.fetchone() is not None

    def analyze_field_injections(
        self,
        fields: List[FieldInfo],
        class_full_name: str
    ) -> List[Relation]:
        """
        分析字段的依赖注入关系

        Args:
            fields: 字段列表
            class_full_name: 所属类的完整名称

        Returns:
            关系列表
        """
        relations = []

        for field in fields:
            # 检查是否有依赖注入注解
            has_inject = any(
                anno in ['@Autowired', '@Resource', '@Inject']
                for anno in field.annotations
            )

            if has_inject:
                # 解析字段类型
                field_type_full = self._resolve_type(field.type, "")

                relations.append(Relation(
                    source_id=class_full_name,
                    target_id=field_type_full if field_type_full in self.symbol_table.values() else None,
                    target_raw=field.type,
                    relation_type="INJECTS",
                    resolved=field_type_full is not None
                ))

        return relations

    def analyze_method_calls(
        self,
        method: MethodInfo,
        class_info: ClassInfo,
        fields: List[FieldInfo],
        imports: Dict[str, str] = None
    ) -> List[Relation]:
        """
        分析方法调用关系（使用新模块）

        Args:
            method: 方法信息
            class_info: 所属类信息
            fields: 类的字段列表
            imports: import语句映射

        Returns:
            关系列表
        """
        if not self.parser or not method.code:
            return []

        if imports is None:
            imports = {}

        # 解析方法体
        content_bytes = bytes(method.code, 'utf-8')
        tree = self.parser.parse(content_bytes)
        root = tree.root_node

        # 1. 创建类型解析器
        type_resolver = TypeResolver(imports, class_info.package)
        type_resolver.set_content_bytes(content_bytes)

        # 2. 提取字段类型和局部变量类型
        field_types = type_resolver.extract_field_types(fields)
        local_types = type_resolver.extract_local_variables(root)

        # 3. 提取方法参数类型并合并到 local_types
        # 从 method.signature 提取参数（简化方法）
        param_types = self._extract_params_from_signature(method.signature, class_info.package, imports)
        local_types.update(param_types)

        # 3. 创建调用分析器
        call_analyzer = CallAnalyzer(
            source_method_id=method.full_name,
            imports=imports,
            current_package=class_info.package,
            field_types=field_types,
            local_types=local_types,
            known_interfaces=self.known_interfaces,
            type_resolver=type_resolver
        )
        call_analyzer.set_content_bytes(content_bytes)

        # 4. 分析调用
        call_infos = call_analyzer.analyze(root)

        # 5. 转换为 Relation
        relations = []
        for call_info in call_infos:
            relation = Relation(
                source_id=method.full_name,
                target_id=call_info.target_id,
                target_raw=call_info.raw,
                relation_type="CALLS",
                line_number=call_info.line,
                resolved=call_info.target_id is not None,
                loop_type=call_info.loop_type,
                loop_id=call_info.loop_id,
                is_interface_call=1 if call_info.is_interface_call else 0,
                lambda_depth=call_info.lambda_depth,
                branch_type=call_info.branch_type,
                branch_id=call_info.branch_id,
                branch_condition=call_info.branch_condition,
                branch_order=call_info.branch_order
            )
            relations.append(relation)

        return relations

    def _generate_virtual_edges(self, interface_call: Relation) -> List[Relation]:
        """
        为接口调用生成虚拟调用边

        当检测到接口调用时：
        1. 查找所有实现该接口方法的类
        2. 为每个实现类创建虚拟调用边

        Args:
            interface_call: 原始接口调用关系

        Returns:
            虚拟调用边列表
        """
        virtual_relations = []

        if not interface_call.target_id:
            return virtual_relations

        # 查找接口方法的所有实现
        implementations = self._find_interface_implementations(interface_call.target_id)

        for impl_method_id, impl_class_name in implementations:
            # 提取分支标识
            branch_label = self._extract_branch_label(impl_class_name)

            # 创建虚拟调用边
            virtual_relation = Relation(
                source_id=interface_call.source_id,
                target_id=impl_method_id,
                target_raw=interface_call.target_raw,
                relation_type="VIRTUAL_CALL",
                line_number=interface_call.line_number,
                resolved=True,
                loop_type=interface_call.loop_type,
                loop_id=interface_call.loop_id,
                is_interface_call=0,  # 虚拟边不是接口调用
                lambda_depth=interface_call.lambda_depth,
                branch_type=interface_call.branch_type,
                branch_id=interface_call.branch_id,
                branch_condition=interface_call.branch_condition,
                branch_order=interface_call.branch_order,
                # 虚拟调用特有字段
                is_virtual=1,
                actual_target_id=impl_method_id,
                via_interface_id=interface_call.target_id
            )
            virtual_relations.append(virtual_relation)

        return virtual_relations

    def _find_interface_implementations(self, interface_method_id: str) -> List[tuple]:
        """
        查找接口方法的所有实现

        Args:
            interface_method_id: 接口方法ID (如 com.example.Handler#handle)

        Returns:
            [(实现方法ID, 实现类名), ...]
        """
        # 分离接口类名和方法名
        if '#' not in interface_method_id:
            return []

        interface_class_id, method_name = interface_method_id.rsplit('#', 1)

        # 查找所有实现该接口的类
        cursor = self.storage.conn.cursor()
        cursor.execute("""
            SELECT source_id
            FROM edges
            WHERE target_id = ?
            AND relation_type = 'IMPLEMENTS'
            AND project_id = ?
        """, (interface_class_id, self.project_id))

        implementations = []
        for row in cursor.fetchall():
            impl_class_id = row['source_id']
            impl_method_id = f"{impl_class_id}#{method_name}"

            # 验证该方法确实存在
            cursor.execute("""
                SELECT 1 FROM nodes
                WHERE id = ?
                AND type = 'method'
                AND project_id = ?
                LIMIT 1
            """, (impl_method_id, self.project_id))

            if cursor.fetchone():
                # 提取实现类的简单名称
                impl_class_name = impl_class_id.split('.')[-1] if '.' in impl_class_id else impl_class_id
                implementations.append((impl_method_id, impl_class_name))

        return implementations

    def _extract_branch_label(self, class_name: str) -> str:
        """
        从类名提取分支标识

        ProductDetailBasicInfoStrategy → BASICINFO
        ProductDetailCardInfoStrategy → CARDINFO
        CardDetailTemplate → CARD
        ListDetailTemplate → LIST

        规则：去掉前缀和后缀，提取核心标识
        """
        # 只取简单类名，不要包名
        simple_name = class_name.split('.')[-1] if '.' in class_name else class_name
        label = simple_name

        # 去掉常见前缀
        prefixes = ['ProductDetail', 'Product', 'Order', 'Train']
        for prefix in prefixes:
            if label.startswith(prefix):
                label = label[len(prefix):]
                break

        # 去掉常见后缀
        suffixes = ['Strategy', 'DetailTemplate', 'Template', 'ServiceImpl', 'Impl', 'Service', 'Handler', 'Processor']
        for suffix in suffixes:
            if label.endswith(suffix):
                label = label[:-len(suffix)]
                break

        return label.upper()

    def _resolve_type(self, type_name: str, package: str) -> Optional[str]:
        """
        解析类型名称到完整类名

        Args:
            type_name: 类型名称（可能是简称或完整名）
            package: 当前包名

        Returns:
            完整类名，如果无法解析则返回 None
        """
        # 已经是完整名称
        if '.' in type_name:
            return type_name

        # 查找符号表
        if type_name in self.symbol_table:
            return self.symbol_table[type_name]

        # 尝试同包类
        if package:
            candidate = f"{package}.{type_name}"
            if candidate in self.symbol_table:
                return candidate

        return None

    def resolve_field_method_calls(self) -> int:
        """
        Phase 2: 解析通过字段调用的方法

        处理类似 productService.getDetailInfo() 的调用：
        1. 找到所有 target_raw 包含 "." 但 target_id 为 NULL 的边
        2. 解析字段类型
        3. 查找对应的方法
        4. 更新 target_id

        Returns:
            成功解析的数量
        """
        import re

        # 获取所有可能是字段方法调用的边
        cursor = self.storage.conn.cursor()
        cursor.execute("""
            SELECT e.id, e.source_id, e.target_id, e.target_raw
            FROM edges e
            WHERE e.project_id = ?
            AND e.relation_type = 'CALLS'
            AND e.target_raw LIKE '%.%(%'
            AND SUBSTR(e.target_raw, 1, 1) BETWEEN 'a' AND 'z'
        """, (self.project_id,))

        unresolved_edges = cursor.fetchall()
        resolved_count = 0

        for edge in unresolved_edges:
            edge_id = edge['id']
            source_id = edge['source_id']
            target_raw = edge['target_raw']

            # 解析调用模式: objectName.methodName(...)
            match = re.match(r'(\w+)\.(\w+)\s*\(', target_raw)
            if not match:
                continue

            field_name = match.group(1)
            method_name = match.group(2)

            # 获取源方法所属的类
            source_class_id = source_id.rsplit('#', 1)[0]
            source_class_simple = source_class_id.rsplit('.', 1)[-1]

            # 查找字段定义
            cursor.execute("""
                SELECT return_type FROM nodes
                WHERE (id = ? OR id = ?) AND type = 'field'
                LIMIT 1
            """, (f"{source_class_id}#{field_name}", f"{source_class_simple}#{field_name}"))

            field_row = cursor.fetchone()
            if not field_row or not field_row['return_type']:
                continue

            field_type = field_row['return_type']

            # 解析字段类型为完整类名
            source_package = source_class_id.rsplit('.', 1)[0] if '.' in source_class_id else ''
            field_full_type = self._resolve_type(field_type, source_package)

            if not field_full_type:
                continue

            # 查找目标方法
            target_method_id = f"{field_full_type}#{method_name}"

            cursor.execute("""
                SELECT id FROM nodes
                WHERE id = ? AND type = 'method'
            """, (target_method_id,))

            if cursor.fetchone():
                # 更新边的 target_id
                cursor.execute("""
                    UPDATE edges
                    SET target_id = ?
                    WHERE id = ?
                """, (target_method_id, edge_id))
                resolved_count += 1
            else:
                # 如果是接口，尝试查找实现类的方法
                cursor.execute("""
                    SELECT nodes.id FROM nodes
                    JOIN edges ON edges.source_id = nodes.parent_id
                    WHERE edges.target_id = ?
                    AND edges.relation_type = 'IMPLEMENTS'
                    AND nodes.name = ?
                    AND nodes.type = 'method'
                    LIMIT 1
                """, (field_full_type, method_name))

                impl_row = cursor.fetchone()
                if impl_row:
                    cursor.execute("""
                        UPDATE edges
                        SET target_id = ?
                        WHERE id = ?
                    """, (impl_row['id'], edge_id))
                    resolved_count += 1

        self.storage.conn.commit()
        return resolved_count

    def save_relations(self, relations: List[Relation]) -> None:
        """
        保存关系到数据库

        Args:
            relations: 关系列表
        """
        edges = []
        for rel in relations:
            edge = {
                'project_id': self.project_id,
                'source_id': rel.source_id,
                'target_id': rel.target_id,
                'target_raw': rel.target_raw,
                'relation_type': rel.relation_type,
                'line_number': rel.line_number,
                'loop_type': rel.loop_type,
                'loop_id': rel.loop_id,
                'is_interface_call': rel.is_interface_call,
                'lambda_depth': rel.lambda_depth,
                'branch_type': rel.branch_type,
                'branch_id': rel.branch_id,
                'branch_condition': rel.branch_condition,
                'branch_order': rel.branch_order,
                # 虚拟调用字段
                'is_virtual': rel.is_virtual,
                'actual_target_id': rel.actual_target_id,
                'via_interface_id': rel.via_interface_id
            }
            edges.append(edge)

        if edges:
            self.storage.save_edges_batch(edges)

    def generate_virtual_call_edges(self) -> int:
        """
        Phase 4: 为所有接口调用生成虚拟调用边

        在所有关系都保存到数据库之后执行,
        查询所有 is_interface_call=1 的边,
        为每条边生成对应的虚拟调用边

        Returns:
            生成的虚拟边数量
        """
        cursor = self.storage.conn.cursor()

        # 查询所有接口调用
        cursor.execute("""
            SELECT *
            FROM edges
            WHERE project_id = ?
            AND relation_type = 'CALLS'
            AND is_interface_call = 1
            AND target_id IS NOT NULL
        """, (self.project_id,))

        interface_calls = cursor.fetchall()
        virtual_edges_count = 0

        for call_row in interface_calls:
            call = dict(call_row)

            # 构造 Relation 对象
            interface_call = Relation(
                source_id=call['source_id'],
                target_id=call['target_id'],
                target_raw=call['target_raw'],
                relation_type=call['relation_type'],
                line_number=call.get('line_number', 0),
                resolved=True,
                loop_type=call.get('loop_type'),
                loop_id=call.get('loop_id'),
                is_interface_call=1,
                lambda_depth=call.get('lambda_depth', 0),
                branch_type=call.get('branch_type'),
                branch_id=call.get('branch_id'),
                branch_condition=call.get('branch_condition'),
                branch_order=call.get('branch_order', 0)
            )

            # 生成虚拟边
            virtual_relations = self._generate_virtual_edges(interface_call)

            # 保存虚拟边
            if virtual_relations:
                self.save_relations(virtual_relations)
                virtual_edges_count += len(virtual_relations)

        return virtual_edges_count

    def _extract_params_from_signature(self, signature: str, package: str, imports: Dict[str, str]) -> Dict[str, str]:
        """
        从方法签名中提取参数类型

        例如: transferVos(ProductDetailContext context)
        返回: {"context": "ProductDetailContext"}

        Args:
            signature: 方法签名
            package: 当前包名
            imports: import映射

        Returns:
            {参数名: 类型}
        """
        import re

        param_types = {}

        # 提取括号内的参数部分
        match = re.search(r'\((.*?)\)', signature)
        if not match:
            return param_types

        params_str = match.group(1).strip()
        if not params_str:
            return param_types

        # 分割参数（简单处理，不处理泛型中的逗号）
        # 例如: "ProductDetailContext context, String name"
        params = [p.strip() for p in params_str.split(',')]

        for param in params:
            parts = param.split()
            if len(parts) >= 2:
                # 最后一个是参数名，之前的是类型
                param_name = parts[-1]
                param_type = ' '.join(parts[:-1])

                # 解析类型为完整类名
                if '.' not in param_type:
                    # 尝试从 imports 解析
                    if param_type in imports:
                        param_type = imports[param_type]
                    elif package:
                        # 尝试同包类
                        param_type = f"{package}.{param_type}"

                param_types[param_name] = param_type

        return param_types
