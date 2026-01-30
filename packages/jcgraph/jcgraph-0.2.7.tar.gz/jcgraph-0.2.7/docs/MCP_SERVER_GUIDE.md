# jcgraph MCP Server 使用指南

## 快速开始

### 1. 安装

**要求**: Python >= 3.10

```bash
# 使用 pip 安装（推荐 Python 3.10+）
pip install jcgraph[mcp]

# 或使用 Python 3.11+ 明确安装
python3.11 -m pip install jcgraph[mcp]
```

#### 配置 PATH 环境变量（可选，推荐）

配置后可以直接使用 `jcgraph` 命令，否则需要使用 `python -m jcgraph.cli.main` 方式调用。

**macOS/Linux (Homebrew Python)**:
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**macOS/Linux (pip --user 安装)**:
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Windows**:
```powershell
# 方式1: 添加 Python Scripts 到 PATH
# 在"系统属性 > 环境变量"中添加: C:\Users\<用户名>\AppData\Local\Programs\Python\Python311\Scripts

# 方式2: 使用 python -m 方式调用（见下文）
```

### 2. 扫描项目

**方式1: 配置 PATH 后使用（推荐）**
```bash
cd /path/to/java/project
jcgraph scan . --name my-project
```

**方式2: 未配置 PATH 时使用**
```bash
cd /path/to/java/project
python3.11 -m jcgraph.cli.main scan . --name my-project
```

### 3. 配置 MCP 客户端

**方式1: 配置 PATH 后使用**
```bash
jcgraph mcp setup --client cursor          # Cursor
jcgraph mcp setup --client claude-cli      # Claude CLI
jcgraph mcp setup --client claude-desktop  # Claude Desktop
```

**方式2: 未配置 PATH 时使用**
```bash
python3.11 -m jcgraph.cli.main mcp setup --client cursor          # Cursor
python3.11 -m jcgraph.cli.main mcp setup --client claude-cli      # Claude CLI
python3.11 -m jcgraph.cli.main mcp setup --client claude-desktop  # Claude Desktop
```

> **提示**: 后续文档中的 `jcgraph` 命令均可替换为 `python3.11 -m jcgraph.cli.main`

---

## 核心工具

### get_call_sequence
获取方法调用时序图（树形结构），返回完整调用链路的结构化 JSON 数据。

**功能**：
- 按调用顺序展开方法调用
- 识别接口/抽象类的多分支实现
- 检测循环调用
- 标注分支条件（if/switch）
- 计算方法重要度评分
- 支持 Lombok、Lambda 表达式

**参数**：
```json
{
  "method_id": "com.example.UserService.login",  // 必需
  "depth": 3,                                     // 可选，默认3，最大10
  "branches": {},                                 // 可选，分支选择
  "min_importance": 50                            // 可选，最小重要度阈值（0-100），默认50
}
```

**智能过滤**：
- 通过 `min_importance` 参数控制节点展开的最小重要度阈值
- 只有 `importance_score >= min_importance` 的节点才会被展开
- 低于阈值的节点会被完全过滤，不会出现在返回数据中
- 推荐值：
  - `30`：展开大部分节点（包括辅助方法）
  - `50`（默认）：只展开重要和关键节点
  - `60`：只展开高重要度节点
  - `80`：只展开关键路径

**返回格式**：
```json
{
  "method": {
    "id": "com.example.UserService.login",
    "name": "login",
    "full_name": "com.example.UserService.login",
    "signature": "public User login(String username, String password)",
    "class_name": "UserService",
    "file_path": "src/.../UserService.java",
    "line_start": 42,
    "line_end": 58,
    "importance_score": 75,
    "importance_level": "CRITICAL"
  },
  "calls": [
    {
      "line": 45,
      "method": {
        "id": "com.example.UserService.validate",
        "name": "validate",
        "importance_score": 50,
        "importance_level": "IMPORTANT"
      },
      "calls": [...],  // 递归嵌套
      "resolved": true,
      "is_branch_point": false,
      "loop_type": null,
      "branch_type": null
    },
    {
      "line": 47,
      "method": {
        "id": "com.example.repository.UserRepository.findByUsername",
        "name": "findByUsername"
      },
      "calls": [...],
      "resolved": true,
      "is_branch_point": true,
      "implementations": [
        {
          "id": "com.example.repository.UserRepositoryImpl.findByUsername",
          "class_name": "UserRepositoryImpl",
          "branch_label": "impl"
        }
      ]
    },
    {
      "line": 52,
      "raw": "log.info(\"User logged in\")",
      "resolved": false  // 未解析的外部调用
    }
  ],
  "branch_points": [
    {
      "abstract_method_id": "com.example.repository.UserRepository.findByUsername",
      "abstract_method_name": "findByUsername",
      "implementations": [...],
      "selected_id": "com.example.repository.UserRepositoryImpl.findByUsername"
    }
  ]
}
```

**数据结构说明**：

**method 节点**：
- `id/name/full_name`: 方法标识
- `signature`: 完整签名
- `importance_score`: 重要度评分（0-100）
- `importance_level`: 重要度等级（CRITICAL/IMPORTANT/NORMAL/AUXILIARY）

**calls 数组（调用列表）**：
- `line`: 调用发生的行号
- `method`: 被调用方法的完整信息
- `calls`: 递归包含的子调用
- `resolved`: 是否解析成功（false=外部依赖）
- `is_branch_point`: 是否有多个实现分支
- `implementations`: 所有可选实现
- `loop_type`: 循环类型（for/while/do-while）
- `branch_type`: 分支类型（if/switch）
- `branch_condition`: 分支条件表达式

**使用场景**：
1. 理解方法执行流程
2. 生成 Mermaid 时序图
3. 提取核心业务逻辑
4. 影响分析
5. 代码审查

---

### get_caller_sequence
获取方法的调用者时序图（反向调用链，自下而上），返回完整的调用者链路的结构化 JSON 数据。

**功能**：
- 展示哪些方法调用了目标方法（反向调用链）
- 支持接口多实现和覆写关系(OVERRIDES)
- 支持虚拟调用边追踪
- 计算方法重要度评分
- 适合影响分析和依赖追踪

**参数**：
```json
{
  "method_id": "com.example.handler.SpecialGoodsHandler.handle",  // 必需
  "depth": 3,                                     // 可选，默认3，最大10
  "min_importance": 50                            // 可选，最小重要度阈值（0-100），默认50
}
```

**智能过滤**：
- 通过 `min_importance` 参数控制节点展开的最小重要度阈值
- 只有 `importance_score >= min_importance` 的节点才会被展开
- 低于阈值的节点会被完全过滤，不会出现在返回数据中
- 推荐值：
  - `30`：展开大部分调用者（包括辅助方法）
  - `50`（默认）：只展开重要和关键调用者
  - `60`：只展开高重要度调用者
  - `80`：只展开关键路径

**返回格式**：
```json
{
  "method": {
    "id": "com.example.handler.SpecialGoodsHandler.handle",
    "name": "handle",
    "full_name": "com.example.handler.SpecialGoodsHandler.handle",
    "signature": "public void handle(Context ctx)",
    "class_name": "SpecialGoodsHandler",
    "file_path": "src/.../SpecialGoodsHandler.java",
    "line_start": 28,
    "line_end": 45,
    "importance_score": 65,
    "importance_level": "IMPORTANT"
  },
  "callers": [
    {
      "method": {
        "id": "com.example.processor.AncillaryProcessor.process",
        "name": "process",
        "importance_score": 70,
        "importance_level": "CRITICAL"
      },
      "relation_type": "CALLS",
      "line": 156,
      "callers": [...],  // 递归嵌套的调用者
      "resolved": true
    },
    {
      "method": {
        "id": "com.example.service.OrderService.getOrderInfo",
        "name": "getOrderInfo",
        "importance_score": 55
      },
      "relation_type": "VIRTUAL_CALL",  // 通过接口或覆写关系
      "line": 89,
      "callers": [...],
      "resolved": true
    }
  ]
}
```

**数据结构说明**：

**method 节点**：
- `id/name/full_name`: 方法标识
- `signature`: 完整签名
- `importance_score`: 重要度评分（0-100）
- `importance_level`: 重要度等级（CRITICAL/IMPORTANT/NORMAL/AUXILIARY）

**callers 数组（调用者列表）**：
- `method`: 调用者方法的完整信息
- `relation_type`: 调用关系类型（CALLS/VIRTUAL_CALL/OVERRIDES）
- `line`: 调用发生的行号
- `callers`: 递归包含的上层调用者
- `resolved`: 是否解析成功

**使用场景**：
1. 影响分析 - 修改一个方法会影响哪些上层调用者
2. 依赖追踪 - 追踪方法被哪些代码路径调用
3. 生成反向调用链时序图
4. 代码重构前的影响评估
5. 理解方法在系统中的使用情况

---

## 辅助工具

### search_code
搜索 Java 类或方法，用于查找方法 ID。

**参数**：
```json
{
  "query": "UserService",        // 必需
  "node_type": "class",          // 可选: class/method/field/interface/enum
  "limit": 20                    // 可选，默认20
}
```

**返回**：文本列表 + JSON 数组

### get_method_code
获取方法源代码。

**参数**：
```json
{
  "method_id": "com.example.UserService.login"  // 必需
}
```

**返回**：格式化的方法信息和 Java 源代码

---

## 典型工作流

### 场景：分析登录流程

```javascript
// 步骤 1：搜索 login 方法
search_code({query: "login", node_type: "method"})
// 返回：com.example.UserService.login

// 步骤 2：获取完整调用链
get_call_sequence({
  method_id: "com.example.UserService.login",
  depth: 3
})
// 返回：树形 JSON，包含 validate → findByUsername → checkPassword

// 步骤 3：查看关键方法源码
get_method_code({method_id: "com.example.UserService.validate"})
// 返回：Java 源代码

// 步骤 4：Agent 解析 JSON 生成时序图或语义描述
```

---

## 已知能力和限制

### ✅ 支持
- 接口/抽象类的多实现分支识别
- 循环结构检测（for/while/do-while）
- 分支条件检测（if/switch）
- Lombok 注解方法（@Data/@Getter/@Setter）
- Lambda 表达式调用
- 方法重载识别
- 嵌套类
- 泛型方法

### ❌ 不支持
- 反射调用（如 `method.invoke()`）
- 动态代理生成的方法
- Spring AOP 拦截器链
- 跨项目依赖（只分析扫描的项目）
- 注解处理器生成的代码
- 代码内容全文搜索

### 性能
- 单次查询：< 1秒（深度3层）
- 数据量：10万行代码的项目，数据库约 50MB
- 深度建议：3-5层（超过5层数据量很大）

---

## 诊断和调试

### 查看数据库统计
```bash
jcgraph stats
```

### 导出诊断报告
```bash
jcgraph diagnose
```

### 查看日志
```bash
tail -f ~/.jcgraph/logs/mcp-$(date +%Y-%m-%d).log
```

### 调试模式
```bash
JCGRAPH_DEBUG=1 jcgraph mcp debug
```

---

## 配置示例

### Cursor 配置
文件：`~/.cursor/mcp.json`
```json
{
  "mcpServers": {
    "jcgraph": {
      "command": "python3.11",
      "args": ["-m", "jcgraph.server.mcp_server"],
      "env": {
        "JCGRAPH_DB": "/path/to/.jcgraph/jcgraph.db"
      }
    }
  }
}
```

### Claude CLI 配置
文件：`~/.claude/mcp_servers.json`
```json
{
  "mcpServers": {
    "jcgraph": {
      "command": "python3.11",
      "args": ["-m", "jcgraph.server.mcp_server"]
    }
  }
}
```

---

## 后续优化

### 计划中的功能
1. **方法权重过滤**：只返回核心逻辑，消除工具类噪音
2. **批量查询**：一次查询多个方法
3. **按注解搜索**：查找所有 @RestController 的类
4. **缓存机制**：加速重复查询
5. **增量更新**：监听代码变化自动更新数据库

### 反馈
问题反馈：https://github.com/your-org/jcgraph/issues

---

## FAQ

**Q: 找不到数据库？**
A: 运行 `jcgraph scan . --name project` 先扫描项目

**Q: 搜索结果为空？**
A: 检查数据库中是否有数据 `jcgraph stats`

**Q: 调用链不完整？**
A: 查看未解析调用 `jcgraph check unresolved`，可能是外部依赖

**Q: 数据量太大？**
A: 降低 depth 参数（推荐 2-3层）

**Q: 如何更新数据？**
A: 重新运行 `jcgraph scan` 会覆盖更新
