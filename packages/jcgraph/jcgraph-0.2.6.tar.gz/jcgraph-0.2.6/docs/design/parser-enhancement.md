# jcgraph 代码解析增强设计

## 一、问题背景

当前解析器存在三个主要问题，需要一起修复后重新扫描。

### 问题1: 循环没有标识

```java
// 实际代码
cardDomainBuilders.stream()
    .filter(b -> b.need(context))
    .forEach(b -> b.build(productDO, logTags));

// 当前显示 (平铺，丢失循环语义)
├─ [L9] cardDomainBuilders.stream()
├─ [L9] b.need(context)
├─ [L16] b.build(productDO, logTags)

// 期望显示
├─ [L9] cardDomainBuilders.stream() [LOOP]
│   ├─ b.need(context)
│   └─ b.build(productDO, logTags)
```

### 问题2: 局部变量接口调用未识别分支

```java
// 代码
CardDomainBuilder b = ...;
b.build(productDO, logTags);  // CardDomainBuilder 是接口，有多个实现

// 当前显示
├─ b.build(productDO, logTags)  // 无法点击，没有分支选择

// 期望显示
├─ b.build() [6个实现 ▼]        // 可点击，可切换分支
```

### 问题3: 接口方法不能点击查看代码

```
CardDomainBuilder 接口的 build() 方法
- resolved = false
- 没有 target_id
- 无法查看代码详情
```

---

## 二、实现前准备

### 2.1 先阅读现有源码

修改前，请先阅读以下文件，理解现有实现：

1. **java_parser.py** - 了解当前 AST 解析逻辑
2. **relation_builder.py** - 了解当前调用关系构建逻辑
3. **storage/sqlite.py** - 了解当前数据存储结构
4. **server/api.py** - 了解当前 API 返回格式

### 2.2 理解现有数据结构

```sql
-- nodes 表
id, name, type, subtype, class_name, ...

-- edges 表  
source_id, target_id, target_raw, relation_type, line_number, resolved, ...
```

---

## 三、数据结构变更

### 3.1 edges 表新增字段

```sql
-- 循环类型: null | 'for' | 'while' | 'foreach' | 'stream'
ALTER TABLE edges ADD COLUMN loop_type TEXT;

-- 循环ID: 同一循环内的调用共享相同 ID，方便前端分组
ALTER TABLE edges ADD COLUMN loop_id TEXT;

-- 是否是接口/抽象方法调用: 0 | 1
ALTER TABLE edges ADD COLUMN is_interface_call INTEGER DEFAULT 0;

-- Lambda 嵌套深度: 0 表示不在 Lambda 内
ALTER TABLE edges ADD COLUMN lambda_depth INTEGER DEFAULT 0;
```

### 3.2 nodes 表确认

确保 subtype 字段值正确：

类的 subtype:
- 'interface': 接口
- 'abstract': 抽象类
- 'class': 普通类
- 'enum': 枚举

方法的 subtype:
- 'abstract': 抽象方法
- 'default': 接口默认方法
- 'static': 静态方法
- 'normal': 普通方法

---

## 四、解析器增强

### 4.1 java_parser.py 增强

#### 4.1.1 循环识别

需要识别以下 AST 节点：

```python
# 循环节点类型映射
LOOP_NODE_TYPES = {
    'for_statement': 'for',
    'enhanced_for_statement': 'foreach',
    'while_statement': 'while',
    'do_statement': 'while',
}

# stream 操作方法名
STREAM_LOOP_METHODS = {'forEach', 'map', 'filter', 'flatMap', 'peek'}
```

解析方法体时：
1. 遍历 AST 节点
2. 遇到循环节点，记录循环类型和生成循环 ID
3. 循环内的所有调用都标记这个 loop_type 和 loop_id
4. 遇到 stream 的 forEach/map 等，同样标记为循环

#### 4.1.2 Lambda 解析

Lambda 表达式内的调用需要：
1. 标记 lambda_depth (嵌套层级)
2. 如果 Lambda 在 stream 操作中，继承 loop 标记
3. Lambda 参数的类型推断 (如 `b -> b.build()` 中 b 的类型)

#### 4.1.3 局部变量类型追踪

新增方法提取局部变量类型：

```python
def _extract_local_variable_types(self, method_body) -> Dict[str, str]:
    """
    提取局部变量及其类型
    
    返回: {"变量名": "类型名"}
    
    识别场景:
    1. 显式声明: CardDomainBuilder b = xxx;
    2. 增强 for: for (CardDomainBuilder b : builders)
    3. try-with-resources: try (InputStream is = ...)
    """
```

### 4.2 relation_builder.py 增强

#### 4.2.1 接口调用识别

分析方法调用时：

1. 获取调用目标的类型 (通过字段类型或局部变量类型)
2. 查询该类型是否是接口或抽象类 (查 nodes 表的 subtype)
3. 如果是接口/抽象类，标记 is_interface_call = 1
4. 同时查找所有实现类 (通过 IMPLEMENTS/EXTENDS 关系)

#### 4.2.2 接口方法解析

确保接口中的方法也被解析并存入 nodes 表：
- 接口方法的 subtype = 'abstract'
- 这样接口方法也有 target_id，可以被点击

#### 4.2.3 循环上下文传递

修改方法体分析逻辑：

```python
def _analyze_method_body(self, method_node, method_id):
    """
    分析方法体，提取调用关系
    
    需要传递循环上下文:
    - 当前是否在循环内
    - 循环类型
    - 循环 ID
    """
```

---

## 五、存储层修改

### 5.1 sqlite.py 修改

#### 5.1.1 建表语句更新

edges 表增加新字段。

#### 5.1.2 save_edge 方法

保存边时包含新字段：loop_type, loop_id, is_interface_call, lambda_depth

#### 5.1.3 查询方法增强

get_callees 等方法返回新字段，用于前端展示。

---

## 六、API 修改

### 6.1 调用链接口返回格式

```json
{
  "method": {
    "id": "...",
    "name": "buildDos"
  },
  "calls": [
    {
      "line": 9,
      "method": {
        "id": "...",
        "name": "build",
        "is_interface_call": true
      },
      "loop_type": "stream",
      "loop_id": "loop_001",
      "implementations": [
        {"id": "...", "class_name": "CardBasicBuilder"},
        {"id": "...", "class_name": "CardPriceBuilder"}
      ]
    }
  ]
}
```

---

## 七、前端修改

### 7.1 循环显示

同一 loop_id 的调用分组显示：

```
├─ [L9] cardDomainBuilders.stream() ──[LOOP]──
│   ├─ b.need(context)
│   └─ b.build() [6个实现 ▼]
│   ──────────────────────────────────────────
```

### 7.2 接口调用显示

is_interface_call = true 的调用：
- 显示实现数量和下拉选择器
- 可点击查看接口方法代码
- 切换实现时加载对应实现的子调用

---

## 八、实现步骤

请按以下顺序实现：

### 步骤1: 阅读源码
- 阅读 java_parser.py，理解 AST 遍历逻辑
- 阅读 relation_builder.py，理解调用关系构建
- 阅读 storage/sqlite.py，理解数据存储

### 步骤2: 修改数据结构
- 修改 sqlite.py 的建表语句，增加新字段
- 修改 save_edge 方法支持新字段

### 步骤3: 增强解析器
- java_parser.py 增加循环识别
- java_parser.py 增加局部变量类型提取
- relation_builder.py 增加接口调用识别
- relation_builder.py 增加循环上下文传递

### 步骤4: 修改 API
- 返回 loop_type, loop_id, is_interface_call
- 接口调用返回 implementations 列表

### 步骤5: 修改前端
- 循环调用分组显示
- 接口调用显示实现选择器

### 步骤6: 测试验证
- 删除旧数据库
- 重新扫描项目
- 验证循环标识正确
- 验证接口调用可点击
- 验证实现分支可切换

---

## 九、验证清单

- [ ] cardDomainBuilders.stream() 显示 [LOOP] 标记
- [ ] 循环内的 b.need() 和 b.build() 缩进在循环下
- [ ] b.build() 显示 [N个实现 ▼]
- [ ] 点击 b.build() 可以查看 CardDomainBuilder.build() 代码
- [ ] 切换实现后显示对应实现类的子调用
- [ ] 接口方法可点击查看代码详情

---

## 十、注意事项

1. 修改解析器后需要重新扫描项目才能生效
2. 扫描前先删除旧的数据库文件
3. 循环 ID 需要全局唯一，可以用 UUID 或计数器
4. 接口调用识别依赖 nodes 表中接口的 subtype 正确
5. Lambda 参数类型推断比较复杂，可以先支持显式类型声明的场景
