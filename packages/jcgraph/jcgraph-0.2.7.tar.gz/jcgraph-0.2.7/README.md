# jcgraph

[![PyPI version](https://badge.fury.io/py/jcgraph.svg)](https://badge.fury.io/py/jcgraph)
[![Python Version](https://img.shields.io/pypi/pyversions/jcgraph.svg)](https://pypi.org/project/jcgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Java 代码知识图谱构建工具** - 通过静态分析构建 Java 代码知识图谱，为 AI 助手提供精准的代码理解能力

## ✨ 核心特性

- 🤖 **MCP Server** - 为 Claude、Cursor 等 AI 工具提供 Java 代码理解能力
- 🔍 **精准解析** - 基于 Tree-sitter 的语法分析，支持类、方法、字段、注解
- 🕸️ **调用链分析** - 完整追踪方法调用关系，支持接口多实现、Lombok
- 📊 **可视化界面** - Web UI 展示调用时序图和代码结构
- 🚀 **快速查询** - SQLite 本地存储，秒级响应

## 📦 安装

```bash
# 基础安装
pip install jcgraph

# 完整功能（包含 Web 服务）
pip install jcgraph[full]

# MCP Server（需要 Python >= 3.10）
pip install jcgraph[mcp]
```

> **提示**: 如果 `pip` 命令无法使用，请使用 `python3 -m pip install jcgraph` 或参考[安装文档](https://github.com/xuelin25/jcgraph/blob/main/docs/MCP_SERVER_GUIDE.md#1-安装)

## 🚀 快速开始

### 1. 扫描 Java 项目

```bash
cd /path/to/java/project
jcgraph scan . --name my-project
```

### 2. 配置 AI 助手（MCP Server）

```bash
# 配置到 Claude Desktop
jcgraph mcp setup --client claude-desktop

# 配置到 Cursor
jcgraph mcp setup --client cursor
```

配置后重启 AI 工具，即可使用以下能力：

- 搜索 Java 类和方法
- 获取方法调用时序图（支持智能过滤）
- 查看方法源代码
- 分析代码结构

### 3. 启动 Web 界面（可选）

```bash
jcgraph serve --port 8080
```

访问 http://localhost:8080 查看可视化界面

## 🤖 MCP Server 工具

配置后，AI 助手可使用以下工具：

| 工具 | 功能 | 参数 |
|------|------|------|
| `get_call_sequence` | 获取方法调用时序图 | `method_id`, `depth`, `min_importance` |
| `search_code` | 搜索类/方法/字段 | `query`, `node_type`, `limit` |
| `get_method_code` | 查看方法源代码 | `method_id` |

**核心功能 - 智能过滤调用时序**：

通过 `min_importance` 参数控制展示粒度：
- `30` - 展开大部分节点（包括辅助方法）
- `50`（默认）- 只展开重要节点
- `60` - 只展开高重要度节点
- `80` - 只展开关键路径

详见：[MCP Server 使用指南](https://github.com/xuelin25/jcgraph/blob/main/docs/MCP_SERVER_GUIDE.md)

## 📚 使用示例

### 在 Claude/Cursor 中提问

```
请分析 UserService.login 方法的调用链，深度3层，只展示重要节点
```

AI 会自动调用 jcgraph 工具，返回结构化的调用时序：

```
login() → validate() → findByUsername() → checkPassword()
```

### 命令行查询

```bash
# 查看统计信息
jcgraph stats

# 检查类信息
jcgraph check class UserService

# 诊断导出
jcgraph diagnose
```

## 🏗️ 支持特性

**语法解析**：
- ✅ 类（class/interface/enum/abstract）
- ✅ 方法（静态/抽象/构造函数）
- ✅ Lombok 注解（@Data, @Getter, @Setter）
- ✅ Lambda 表达式
- ✅ 泛型参数

**关系分析**：
- ✅ 继承（extends）
- ✅ 实现（implements）
- ✅ 方法调用（包括链式调用）
- ✅ 依赖注入（@Autowired, @Resource）
- ✅ 接口多实现识别
- ✅ 循环检测（for/while）
- ✅ 分支检测（if/switch）

## 📖 文档

- [MCP Server 使用指南](https://github.com/xuelin25/jcgraph/blob/main/docs/MCP_SERVER_GUIDE.md) - 完整安装配置教程
- [MCP Server 快速开始](https://github.com/xuelin25/jcgraph/blob/main/docs/MCP_QUICKSTART.md)

## 🔧 系统要求

- Python >= 3.9（基础功能）
- Python >= 3.10（MCP Server）
- Java 8+ 项目

## 📝 更新日志

### v0.2.4

- ✨ 解耦 MCP Server 和 FastAPI 依赖
- ✨ 新增智能节点过滤（min_importance 参数）
- 📚 完善安装和配置文档
- 🐛 修复静态文件打包问题

### v0.2.0

- ✨ 新增 MCP Server 支持
- ✨ 新增日志和诊断工具
- ✨ 新增自动配置命令
- 📚 完整的使用文档

## 🤝 贡献

欢迎提交 [Issue](https://github.com/xuelin25/jcgraph/issues) 和 Pull Request！

## 📄 License

MIT License

## 🔗 链接

- GitHub: https://github.com/xuelin25/jcgraph
- PyPI: https://pypi.org/project/jcgraph/
- Model Context Protocol: https://modelcontextprotocol.io

---

**为 Java 开发者和 AI 辅助编程而生**
