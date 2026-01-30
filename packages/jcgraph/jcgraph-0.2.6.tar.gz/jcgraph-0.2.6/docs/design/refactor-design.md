# jcgraph Scanner 模块重构设计

## 一、重构目标

当前 scanner 模块代码职责混乱，难以维护和扩展。需要拆分为职责单一的子模块。

### 当前问题

```
java_parser.py:
  - AST 解析
  - 类型提取
  - 部分关系识别
  职责过多，代码臃肿

relation_builder.py:
  - 调用分析
  - 循环检测
  - 接口识别
  - 关系构建
  各种逻辑堆积，难以维护
```

### 重构后结构

```
scanner/
  ├── __init__.py
  ├── java_parser.py      # 纯 AST 解析
  ├── type_resolver.py    # 类型推断
  ├── call_analyzer.py    # 调用分析
  ├── loop_detector.py    # 循环识别
  └── relation_builder.py # 组装协调
```

---

## 二、模块职责定义

### 2.1 java_parser.py

**职责**: 纯 AST 解析，输出结构化数据

**输入**: Java 源码文件路径

**输出**: ParseResult 数据结构

```python
@dataclass
class FieldInfo:
    name: str
    type_name: str           # List<CardDomainBuilder>
    generic_type: str        # CardDomainBuilder (提取的泛型参数)
    line_number: int
    annotations: List[str]

@dataclass
class MethodInfo:
    name: str
    signature: str
    return_type: str
    parameters: List[ParameterInfo]
    body_node: Any           # AST 节点，供其他模块分析
    line_start: int
    line_end: int
    annotations: List[str]
    modifiers: List[str]     # public, static, abstract 等

@dataclass
class ClassInfo:
    name: str
    full_name: str
    type: str                # class, interface, enum, abstract
    extends: str
    implements: List[str]
    fields: List[FieldInfo]
    methods: List[MethodInfo]
    file_path: str

@dataclass
class ParseResult:
    classes: List[ClassInfo]
    imports: Dict[str, str]  # {简单名: 全限定名}
```

**不做的事**:
- 不做类型推断
- 不做调用关系分析
- 不做循环检测

---

### 2.2 type_resolver.py

**职责**: 类型推断，构建类型映射表

**输入**: 
- ClassInfo (字段信息)
- MethodInfo (参数信息)
- AST 节点 (局部变量声明)

**输出**: TypeContext 类型上下文

```python
@dataclass
class TypeContext:
    # 字段类型映射
    field_types: Dict[str, str]          # {字段名: 类型}
    field_generic_types: Dict[str, str]  # {字段名: 泛型参数类型}
    
    # 局部变量类型映射
    local_types: Dict[str, str]          # {变量名: 类型}
    
    # Lambda 参数类型映射
    lambda_param_types: Dict[str, str]   # {参数名: 类型}

class TypeResolver:
    def __init__(self, class_info: ClassInfo, imports: Dict[str, str]):
        pass
    
    def resolve_field_types(self) -> Dict[str, str]:
        """提取所有字段的类型"""
        pass
    
    def extract_generic_type(self, type_str: str) -> Optional[str]:
        """
        从泛型类型中提取参数类型
        List<CardDomainBuilder> -> CardDomainBuilder
        Map<String, User> -> User (取 value 类型)
        """
        pass
    
    def resolve_local_variables(self, method_body: Any) -> Dict[str, str]:
        """提取方法内局部变量的类型"""
        pass
    
    def infer_lambda_param_type(self, 
                                 collection_var: str, 
                                 lambda_param: str) -> Optional[str]:
        """
        推断 Lambda 参数类型
        
        collection.stream().filter(x -> ...)
        x 的类型 = collection 的泛型参数
        """
        pass
    
    def get_type(self, var_name: str) -> Optional[str]:
        """获取变量的类型 (优先级: lambda > local > field)"""
        pass
```

---

### 2.3 loop_detector.py

**职责**: 识别循环结构

**输入**: 方法体 AST 节点

**输出**: 循环信息列表

```python
@dataclass
class LoopInfo:
    loop_id: str             # UUID
    loop_type: str           # 'for', 'foreach', 'while', 'stream'
    start_line: int
    end_line: int
    iterator_var: str        # 循环变量名 (如 for 中的 i, foreach 中的 item)
    collection_var: str      # 被遍历的集合变量名 (用于类型推断)

class LoopDetector:
    # 循环节点类型
    LOOP_NODE_TYPES = {
        'for_statement': 'for',
        'enhanced_for_statement': 'foreach',
        'while_statement': 'while',
        'do_statement': 'while',
    }
    
    # Stream 方法名
    STREAM_METHODS = {'stream', 'parallelStream'}
    STREAM_TERMINAL_METHODS = {'forEach', 'map', 'filter', 'flatMap', 'peek', 'reduce', 'collect', 'toList'}
    
    def __init__(self, method_body: Any):
        pass
    
    def detect_loops(self) -> List[LoopInfo]:
        """检测所有循环 (for/while/foreach)"""
        pass
    
    def detect_stream_chains(self) -> List[LoopInfo]:
        """检测 stream 链式调用"""
        pass
    
    def get_loop_at_line(self, line: int) -> Optional[LoopInfo]:
        """获取指定行所在的循环"""
        pass
    
    def is_in_loop(self, line: int) -> bool:
        """判断某行是否在循环内"""
        pass
```

---

### 2.4 call_analyzer.py

**职责**: 分析方法调用

**输入**: 
- 方法体 AST 节点
- TypeContext 类型上下文
- LoopInfo 循环信息

**输出**: 调用信息列表

```python
@dataclass
class CallInfo:
    line: int
    caller: str              # 调用者 (如 b, this, ClassName)
    caller_type: str         # 调用者的类型
    method_name: str         # 方法名
    arguments: List[str]     # 参数
    raw: str                 # 原始文本 (如 b.need(context))
    
    # 循环相关
    loop_type: Optional[str]
    loop_id: Optional[str]
    lambda_depth: int        # Lambda 嵌套深度
    
    # 接口相关
    is_interface_call: bool
    
class CallAnalyzer:
    def __init__(self, 
                 method_body: Any,
                 type_context: TypeContext,
                 loop_infos: List[LoopInfo],
                 known_interfaces: Set[str]):
        pass
    
    def analyze(self) -> List[CallInfo]:
        """分析所有方法调用"""
        pass
    
    def _extract_calls_from_node(self, node: Any, 
                                  lambda_depth: int = 0) -> List[CallInfo]:
        """从 AST 节点提取调用"""
        pass
    
    def _analyze_lambda(self, lambda_node: Any, 
                        collection_var: str,
                        lambda_depth: int) -> List[CallInfo]:
        """分析 Lambda 表达式内的调用"""
        pass
    
    def _is_interface_call(self, caller_type: str) -> bool:
        """判断是否是接口方法调用"""
        pass
```

---

### 2.5 relation_builder.py

**职责**: 协调各模块，组装最终关系

**输入**: ParseResult 和各模块输出

**输出**: 可存储的 Edge 列表

```python
@dataclass
class Edge:
    source_id: str
    target_id: Optional[str]
    target_raw: str
    relation_type: str       # CALLS, IMPLEMENTS, EXTENDS, OVERRIDES
    line_number: int
    resolved: bool
    
    # 扩展字段
    loop_type: Optional[str]
    loop_id: Optional[str]
    lambda_depth: int
    is_interface_call: bool

class RelationBuilder:
    def __init__(self, storage, project_id: str):
        self.storage = storage
        self.project_id = project_id
        self.known_interfaces: Set[str] = set()
    
    def build(self, parse_result: ParseResult) -> List[Edge]:
        """
        构建所有关系
        
        流程:
        1. 从 parse_result 提取类信息
        2. 构建 TypeContext
        3. 检测循环
        4. 分析调用
        5. 组装 Edge
        """
        pass
    
    def _build_class_edges(self, class_info: ClassInfo) -> List[Edge]:
        """构建类级别关系 (EXTENDS, IMPLEMENTS)"""
        pass
    
    def _build_method_edges(self, 
                            method_info: MethodInfo,
                            class_info: ClassInfo) -> List[Edge]:
        """构建方法调用关系"""
        pass
    
    def _resolve_target(self, call_info: CallInfo) -> Optional[str]:
        """解析调用目标的完整 ID"""
        pass
```

---

## 三、数据流

```
源码文件
    │
    ▼
┌─────────────────┐
│  java_parser    │ ──→ ParseResult (类、方法、字段、AST)
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  type_resolver  │ ──→ TypeContext (类型映射表)
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  loop_detector  │ ──→ List[LoopInfo] (循环信息)
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  call_analyzer  │ ──→ List[CallInfo] (调用信息)
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ relation_builder│ ──→ List[Edge] (最终关系)
└─────────────────┘
    │
    ▼
  Storage
```

---

## 四、重构步骤

### 步骤1: 创建新模块文件

```bash
# 在 scanner 目录下创建新文件
touch src/jcgraph/scanner/type_resolver.py
touch src/jcgraph/scanner/call_analyzer.py
touch src/jcgraph/scanner/loop_detector.py
```

### 步骤2: 定义数据结构

在各模块中定义 dataclass:
- FieldInfo, MethodInfo, ClassInfo, ParseResult
- TypeContext
- LoopInfo
- CallInfo
- Edge

### 步骤3: 重构 java_parser.py

1. 保留 AST 解析逻辑
2. 移除类型推断逻辑 → type_resolver
3. 移除调用分析逻辑 → call_analyzer
4. 确保输出 ParseResult

### 步骤4: 实现 type_resolver.py

1. 从旧代码中提取类型相关逻辑
2. 实现泛型提取
3. 实现 Lambda 参数类型推断

### 步骤5: 实现 loop_detector.py

1. 从旧代码中提取循环检测逻辑
2. 增加 stream 链检测

### 步骤6: 实现 call_analyzer.py

1. 从旧代码中提取调用分析逻辑
2. 集成类型上下文和循环信息

### 步骤7: 重构 relation_builder.py

1. 改为协调角色
2. 调用各子模块
3. 组装最终结果

### 步骤8: 更新 CLI 调用

修改 scan 命令，使用重构后的模块

### 步骤9: 测试验证

1. 删除数据库
2. 重新扫描
3. 验证结果一致

---

## 五、验证清单

重构完成后验证:

- [ ] 扫描不报错
- [ ] 类和方法正确识别
- [ ] 调用关系正确
- [ ] 循环标识正确 (FOREACH)
- [ ] 抽象方法分支正确
- [ ] 重要度计算正确
- [ ] Web 页面显示正常

---

## 六、注意事项

1. **保持功能不变**
   - 重构只是拆分代码
   - 不要同时加新功能
   - 每步都要测试

2. **保留旧代码备份**
   - 重构前备份
   - 出问题可回滚

3. **单元测试**
   - 各模块独立可测试
   - 重构后补充测试

4. **渐进式重构**
   - 一个模块一个模块来
   - 不要一次性全改

---

## 七、后续扩展

重构完成后，新功能容易加入:

1. **Stream + Lambda 支持**
   - 在 loop_detector 中增加 stream 检测
   - 在 type_resolver 中增加 Lambda 类型推断
   - 在 call_analyzer 中处理 Lambda 内调用

2. **更多语言支持**
   - 新增 kotlin_parser.py
   - 复用 type_resolver, call_analyzer 等

3. **增量扫描**
   - java_parser 支持单文件解析
   - relation_builder 支持增量更新
