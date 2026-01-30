# jcgraph MCP Server - 快速开始

## 5分钟快速上手

### 1. 环境准备

**要求**: Python 3.10+

```bash
# 检查 Python 版本
python3 --version

# 如果版本过低，安装 Python 3.11
# macOS:
brew install python@3.11

# Linux (Ubuntu/Debian):
sudo apt install python3.11
```

### 2. 安装 jcgraph

```bash
# 安装 jcgraph 及 MCP 支持
pip install jcgraph[mcp]

# 或使用特定 Python 版本
python3.11 -m pip install jcgraph[mcp]
```

### 3. 扫描 Java 项目

```bash
# 进入你的 Java 项目目录
cd /path/to/your/java/project

# 扫描项目
jcgraph scan . --name my-project

# 查看统计（可选）
jcgraph stats
```

### 4. 配置到客户端

#### Cursor

```bash
# 自动配置
jcgraph mcp setup --client cursor

# 重启 Cursor
```

#### Claude CLI

```bash
# 自动配置
jcgraph mcp setup --client claude-cli

# 测试
claude "使用 jcgraph 搜索 UserService 类"
```

#### Claude Desktop

```bash
# 自动配置
jcgraph mcp setup --client claude-desktop

# 重启 Claude Desktop
```

### 5. 开始使用

在 Cursor 或 Claude CLI 中，尝试以下指令：

```
# 搜索代码
"使用 jcgraph 搜索 UserService 类"
"查找包含 login 的方法"

# 查看调用链
"使用 jcgraph 查看 UserService.login 方法的调用链"
"分析 processOrder 方法调用了哪些方法"

# 查看类结构
"用 jcgraph 显示 User 类的结构"
"查看 ProductRepository 接口有哪些方法"

# 获取方法详情
"使用 jcgraph 获取 login 方法的源代码"
```

---

## 验证安装

```bash
# 查看命令
jcgraph --help

# 检查配置状态
jcgraph mcp status

# 查看数据库统计
jcgraph stats
```

预期输出：

```
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 客户端     ┃ 状态                           ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ cursor     │ ✓ 已配置                       │
│ claude-cli │ ✓ 已配置                       │
└────────────┴────────────────────────────────┘
```

---

## 常见问题

### "MCP SDK 未安装"

```bash
# 检查 Python 版本
python3 --version  # 需要 >= 3.10

# 重新安装
python3.11 -m pip install jcgraph[mcp]
```

### "未找到数据库"

```bash
# 检查数据库
ls -la ~/.jcgraph/
ls -la .jcgraph/

# 重新扫描
jcgraph scan . --name my-project
```

### 客户端看不到工具

1. 检查配置：`jcgraph mcp status`
2. 重启客户端（Cursor/Claude CLI/Claude Desktop）
3. 查看客户端日志

---

## 下一步

- 📖 阅读[完整文档](./MCP_SERVER_GUIDE.md)
- 🔧 使用诊断工具: `jcgraph check class YourClass`
- 🐛 调试模式: `jcgraph mcp debug`

---

## 特性亮点

✨ **语义级代码理解** - 不只是文本搜索
🔗 **完整调用链分析** - 向上/向下追溯
📦 **类型解析** - 自动解析依赖关系
🎯 **精准查询** - 基于知识图谱

---

Happy Coding! 🚀
