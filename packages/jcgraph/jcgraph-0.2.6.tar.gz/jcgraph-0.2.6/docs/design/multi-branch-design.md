# jcgraph 多分支调用链支持 - 设计与实现文档

## 目标

支持抽象方法/接口方法的多实现分支展示，在时序图中实现节点级分支切换。

## 验收标准

```
1. 时序图中，抽象方法节点显示 [N个实现 ▼]
2. 点击下拉框可切换到不同实现
3. 切换后展示该实现的完整调用链
4. 默认展示第一个实现
5. 多层分支各自独立切换
```

---

## 一、数据层设计

### 1.1 识别抽象/接口方法

**修改 java_parser.py**

解析方法时识别 abstract 修饰符：

```python
# 在 _parse_method 中增加
def _parse_method(self, node, class_name):
    # ... 已有逻辑
    
    # 检查是否是抽象方法
    modifiers = self._get_modifiers(node)
    is_abstract = 'abstract' in modifiers
    
    return MethodInfo(
        # ... 已有字段
        subtype='abstract' if is_abstract else 'normal',
    )
```

同时识别接口中的方法（接口方法默认是抽象的）：

```python
# 如果父类是 interface，所有方法默认 subtype='abstract'
# 除非方法有 default 修饰符
```

### 1.2 新增 OVERRIDES 关系

**修改 relation_builder.py**

新增方法：

```python
def analyze_override_relations(self, class_info: ClassInfo, methods: List[MethodInfo]) -> List[Relation]:
    """
    分析方法覆写关系
    
    识别条件：
    1. 方法有 @Override 注解
    2. 父类/接口中存在同签名方法
    
    生成：
    source_id: 子类方法 (CardDetailTemplate#buildDos)
    target_id: 父类方法 (ProductDetailTemplate#buildDos)  
    relation_type: 'OVERRIDES'
    """
    relations = []
    
    for method in methods:
        # 检查是否有 @Override 注解
        if '@Override' not in method.annotations:
            continue
        
        # 查找父类/接口中的同名方法
        parent_method_id = self._find_parent_method(
            class_info, 
            method.name, 
            method.signature
        )
        
        if parent_method_id:
            relations.append(Relation(
                source_id=f"{class_info.full_name}#{method.name}",
                target_id=parent_method_id,
                relation_type='OVERRIDES',
                resolved=True,
            ))
    
    return relations

def _find_parent_method(self, class_info, method_name, signature) -> Optional[str]:
    """
    在父类/接口中查找同名方法
    
    查找顺序：
    1. extends 的父类
    2. implements 的接口
    """
    # 查父类
    if class_info.extends:
        parent_full_name = self._resolve_type(class_info.extends)
        if parent_full_name:
            parent_method_id = f"{parent_full_name}#{method_name}"
            if self._method_exists(parent_method_id):
                return parent_method_id
    
    # 查接口
    for interface in class_info.implements:
        interface_full_name = self._resolve_type(interface)
        if interface_full_name:
            interface_method_id = f"{interface_full_name}#{method_name}"
            if self._method_exists(interface_method_id):
                return interface_method_id
    
    return None
```

### 1.3 存储分支标识

**新增 branch_label 字段或使用类名提取**

简化方案：从类名提取分支标识

```python
def _extract_branch_label(self, class_name: str) -> str:
    """
    从类名提取分支标识
    
    CardDetailTemplate → CARD
    ListDetailTemplate → LIST
    ProductHeaderTemplate → HEADER
    
    规则：去掉 Template/Impl/Service 等后缀，取前面部分
    """
    suffixes = ['DetailTemplate', 'Template', 'ServiceImpl', 'Impl', 'Service']
    label = class_name
    for suffix in suffixes:
        if label.endswith(suffix):
            label = label[:-len(suffix)]
            break
    return label.upper()
```

### 1.4 edges 表结构确认

```sql
-- 已有表结构足够，只需新增 relation_type = 'OVERRIDES'
-- 可选：增加 branch_label 字段

ALTER TABLE edges ADD COLUMN branch_label TEXT;

-- OVERRIDES 边示例：
-- source_id: com.ctrip.xxx.CardDetailTemplate#buildDos
-- target_id: com.ctrip.xxx.ProductDetailTemplate#buildDos
-- relation_type: OVERRIDES
-- branch_label: CARD
```

---

## 二、查询层设计

### 2.1 获取方法的所有实现

**storage/sqlite.py 新增方法**

```python
def get_implementations(self, method_id: str) -> List[Dict]:
    """
    获取抽象方法的所有实现
    
    Args:
        method_id: 抽象方法ID，如 ProductDetailTemplate#buildDos
        
    Returns:
        [
            {
                "id": "CardDetailTemplate#buildDos",
                "class_name": "CardDetailTemplate", 
                "branch_label": "CARD"
            },
            ...
        ]
    """
    sql = """
        SELECT 
            e.source_id as id,
            n.class_name,
            e.branch_label
        FROM edges e
        JOIN nodes n ON e.source_id = n.id
        WHERE e.target_id = ? 
        AND e.relation_type = 'OVERRIDES'
        ORDER BY e.branch_label
    """
    return self.execute(sql, [method_id])
```

### 2.2 修改调用链查询

**storage/sqlite.py 修改 get_callees**

```python
def get_callees(self, node_id: str, depth: int, branch_selections: Dict[str, str] = None) -> Dict:
    """
    获取调用链，支持分支选择
    
    Args:
        node_id: 起始方法ID
        depth: 最大深度
        branch_selections: 分支选择 {抽象方法ID: 选中的实现ID}
                          如 {"ProductDetailTemplate#buildDos": "CardDetailTemplate#buildDos"}
    
    Returns:
        {
            "nodes": [...],
            "edges": [...],
            "branch_points": [...]  # 分支点信息
        }
    """
    branch_selections = branch_selections or {}
    visited = set()
    nodes = []
    edges = []
    branch_points = []  # 记录所有分支点
    
    def _traverse(nid, current_depth):
        if current_depth > depth or nid in visited:
            return
        visited.add(nid)
        
        # 获取节点信息
        node = self.get_node(nid)
        if node:
            nodes.append(node)
        
        # 检查是否是抽象方法（分支点）
        if node and node.get('subtype') == 'abstract':
            implementations = self.get_implementations(nid)
            if implementations:
                branch_points.append({
                    "method_id": nid,
                    "implementations": implementations,
                    "selected": branch_selections.get(nid, implementations[0]['id'])
                })
                
                # 只遍历选中的实现
                selected_impl = branch_selections.get(nid, implementations[0]['id'])
                _traverse(selected_impl, current_depth)  # 不增加深度，替换节点
                return
        
        # 获取出边
        method_edges = self.get_edges_from(nid)
        for edge in method_edges:
            edges.append(edge)
            if edge['target_id']:
                _traverse(edge['target_id'], current_depth + 1)
    
    _traverse(node_id, 0)
    
    return {
        "nodes": nodes,
        "edges": edges,
        "branch_points": branch_points
    }
```

---

## 三、API层设计

### 3.1 修改调用链接口

**server/api.py**

```python
@app.get("/api/graph/callees/{node_id}")
async def get_callees(
    node_id: str,
    depth: int = 3,
    branches: str = None  # JSON格式的分支选择
):
    """
    获取向下调用链
    
    参数：
        node_id: 方法ID
        depth: 深度
        branches: 分支选择，JSON格式
                  如 '{"ProductDetailTemplate#buildDos":"CardDetailTemplate#buildDos"}'
    """
    branch_selections = {}
    if branches:
        try:
            branch_selections = json.loads(branches)
        except:
            pass
    
    result = storage.get_callees(node_id, depth, branch_selections)
    
    return {
        "root": node_id,
        "nodes": result["nodes"],
        "edges": result["edges"],
        "branch_points": result["branch_points"]  # 新增：分支点信息
    }
```

### 3.2 API返回格式

```json
{
    "root": "IntlOfflineServiceImpl#getProductCardInfo",
    "nodes": [
        {"id": "...", "name": "getProductCardInfo", "subtype": "normal"},
        {"id": "...", "name": "buildDos", "subtype": "abstract"},
        {"id": "...", "name": "buildDos", "class_name": "CardDetailTemplate", "subtype": "normal"}
    ],
    "edges": [
        {"source_id": "...", "target_id": "...", "line_number": 5}
    ],
    "branch_points": [
        {
            "method_id": "ProductDetailTemplate#buildDos",
            "implementations": [
                {"id": "CardDetailTemplate#buildDos", "class_name": "CardDetailTemplate", "branch_label": "CARD"},
                {"id": "ListDetailTemplate#buildDos", "class_name": "ListDetailTemplate", "branch_label": "LIST"},
                {"id": "HeaderDetailTemplate#buildDos", "class_name": "HeaderDetailTemplate", "branch_label": "HEADER"}
            ],
            "selected": "CardDetailTemplate#buildDos"
        }
    ]
}
```

---

## 四、前端设计

### 4.1 时序图节点渲染

```javascript
function renderSequenceNode(node, branchPoints) {
    // 检查是否是分支点
    const branchPoint = branchPoints.find(bp => bp.method_id === node.id);
    
    if (branchPoint) {
        // 渲染带下拉框的节点
        return `
            <div class="sequence-node branch-point">
                <span class="method-name">${node.name}()</span>
                <select class="branch-selector" data-method-id="${node.id}">
                    ${branchPoint.implementations.map(impl => `
                        <option value="${impl.id}" ${impl.id === branchPoint.selected ? 'selected' : ''}>
                            ${impl.branch_label}
                        </option>
                    `).join('')}
                </select>
            </div>
        `;
    } else {
        // 普通节点
        return `
            <div class="sequence-node">
                <span class="method-name">${node.name}()</span>
                <span class="class-name">${node.class_name}</span>
            </div>
        `;
    }
}
```

### 4.2 分支切换交互

```javascript
// 监听分支切换
document.addEventListener('change', async (e) => {
    if (e.target.classList.contains('branch-selector')) {
        const methodId = e.target.dataset.methodId;
        const selectedImpl = e.target.value;
        
        // 更新分支选择
        branchSelections[methodId] = selectedImpl;
        
        // 重新加载调用链
        await loadCallGraph(currentNodeId, currentDepth, branchSelections);
    }
});

async function loadCallGraph(nodeId, depth, branchSelections = {}) {
    const branchesParam = Object.keys(branchSelections).length > 0 
        ? `&branches=${encodeURIComponent(JSON.stringify(branchSelections))}`
        : '';
    
    const response = await fetch(
        `/api/graph/callees/${encodeURIComponent(nodeId)}?depth=${depth}${branchesParam}`
    );
    const data = await response.json();
    
    renderSequenceGraph(data);
}
```

### 4.3 展示效果

```
getProductCardInfo()
├─ [L5] convertProductDetailParam()
├─ [L6] getDetailInfo()
│   ├─ [L29] getProductDetailTemplate()
│   └─ [L40] execute()
│        ├─ preProcess()
│        ├─ buildDos() [CARD ▼]              ← 分支点，可切换
│        │    └─ buildCardDos()              ← CardDetailTemplate的具体实现
│        │         └─ assembleCardInfo()
│        └─ transferVos() [CARD ▼]           ← 另一个分支点
│             └─ transferCardVos()
└─ [L7] setData()

下拉框选项：
┌─────────────┐
│ ● CARD      │  ← 当前选中
│ ○ LIST      │
│ ○ HEADER    │
│ ○ DETAIL    │
│ ○ REFUND    │
│ ○ CHANGE    │
└─────────────┘
```

---

## 五、CLI 集成修改

### 5.1 scan 命令增加 OVERRIDES 分析

**cli/main.py**

```python
@app.command()
def scan(path: str, name: str = None):
    # ... 已有步骤 1-4
    
    # 步骤 5: 分析覆写关系
    console.print("步骤 5/5: 分析覆写关系...")
    override_count = 0
    
    for result in parse_results:
        for class_info in result.classes:
            methods = [m for m in result.methods if m.class_name == class_info.name]
            
            override_relations = relation_builder.analyze_override_relations(
                class_info, 
                methods
            )
            
            for relation in override_relations:
                storage.save_edge({
                    'project_id': project_id,
                    'source_id': relation.source_id,
                    'target_id': relation.target_id,
                    'relation_type': 'OVERRIDES',
                    'branch_label': relation_builder._extract_branch_label(
                        relation.source_id.split('#')[0].split('.')[-1]
                    ),
                    'resolved': 1,
                })
                override_count += 1
    
    console.print(f"✓ 覆写关系: {override_count} 条")
```

---

## 六、开发顺序

```
1. 数据层 (1天)
   □ java_parser: 识别 abstract 方法
   □ relation_builder: 新增 analyze_override_relations
   □ relation_builder: 实现 _find_parent_method
   □ relation_builder: 实现 _extract_branch_label
   □ storage: 新增 get_implementations 方法
   □ storage: 修改 get_callees 支持分支选择

2. API层 (0.5天)
   □ 修改 /api/graph/callees 接口
   □ 新增 branches 参数
   □ 返回 branch_points 信息

3. 前端 (1天)
   □ 时序图渲染分支节点
   □ 下拉框组件
   □ 分支切换交互
   □ 重新加载逻辑

4. CLI集成 (0.5天)
   □ scan 命令增加覆写分析步骤
   □ 统计输出

5. 测试验证 (0.5天)
   □ 重新扫描项目
   □ 验证 buildDos 6个实现都能识别
   □ 验证分支切换功能
   □ 验证多层分支独立切换

总计: 3.5天
```

---

## 七、验证清单

```
□ buildDos() 显示 [6个实现 ▼]
□ 点击下拉框显示: CARD, LIST, HEADER, DETAIL, REFUND, CHANGE
□ 选择 CARD → 展示 CardDetailTemplate.buildDos() 的调用链
□ 选择 LIST → 展示 ListDetailTemplate.buildDos() 的调用链
□ transferVos() 等其他抽象方法也能独立切换
□ 多层分支互不影响
□ 默认展示第一个实现
```

---

## 八、给 CLI 的完整提示词

```
我需要为 jcgraph 实现多分支调用链支持。

当前问题：
- buildDos() 是抽象方法，有6个实现
- 时序图只显示抽象方法，没有展示具体实现
- 无法切换查看不同实现的调用链

目标效果：
- 抽象方法节点显示 [CARD ▼] 下拉框
- 可切换到不同实现
- 切换后展示该实现的完整调用链
- 多层分支独立切换

请按以下顺序实现：

### 第一步：数据层

1. java_parser.py
   - 识别 abstract 修饰符
   - 方法 subtype = 'abstract' / 'normal'

2. relation_builder.py 新增：
   - analyze_override_relations(class_info, methods) 方法
   - 识别 @Override 注解的方法
   - 查找父类/接口中的同名方法
   - 创建 OVERRIDES 边
   - _extract_branch_label() 从类名提取分支标识

3. storage/sqlite.py 新增：
   - edges 表增加 branch_label 字段
   - get_implementations(method_id) 方法
   - 修改 get_callees() 支持 branch_selections 参数

### 第二步：API层

修改 /api/graph/callees/{node_id}：
- 新增 branches 参数 (JSON格式的分支选择)
- 返回 branch_points 数组（分支点信息）

### 第三步：前端

修改时序图页面：
- 分支点节点显示下拉框
- 监听 change 事件
- 切换时重新请求 API（带 branches 参数）
- 重新渲染时序图

### 第四步：CLI

修改 scan 命令：
- 增加分析覆写关系步骤
- 保存 OVERRIDES 边和 branch_label
- 输出统计

完成后告诉我，我会重新扫描验证。
```
