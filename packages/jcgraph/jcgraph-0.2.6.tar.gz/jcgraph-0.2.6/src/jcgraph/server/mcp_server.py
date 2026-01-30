"""jcgraph MCP Server - 为 Claude CLI、Cursor 等提供 Java 代码分析能力

本模块需要 Python 3.10+ 和 mcp SDK
安装方式: pip install mcp
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Any

# MCP SDK 导入（需要 Python 3.10+）
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError:
    print("错误: MCP SDK 未安装或 Python 版本不满足要求 (需要 3.10+)", file=sys.stderr)
    print("安装方式: pip install mcp", file=sys.stderr)
    sys.exit(1)

from jcgraph.storage.sqlite import Storage
from jcgraph.utils.db_finder import find_database, get_default_database
from jcgraph.utils.logger import setup_logger

# 配置日志（使用新的日志模块）
debug_mode = bool(os.environ.get('JCGRAPH_DEBUG'))
logger = setup_logger("jcgraph.mcp", debug=debug_mode)

# 创建 MCP Server 实例
app = Server("jcgraph")

# 全局 storage 实例
_storage: Optional[Storage] = None


def get_storage() -> Storage:
    """获取或初始化 storage 实例"""
    global _storage
    if _storage is None:
        db_path = find_database()
        if db_path is None:
            db_path = get_default_database()
            logger.warning(f"未找到数据库，使用默认路径: {db_path}")
        else:
            logger.info(f"使用数据库: {db_path}")

        _storage = Storage(db_path)
    return _storage


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的 MCP 工具"""
    return [
        Tool(
            name="get_call_sequence",
            description=(
                "【核心工具】获取方法调用时序图（树形结构）。"
                "返回完整的调用链路，包括：调用顺序、分支点、循环、方法重要度评分。"
                "支持接口多实现、Lombok、Lambda表达式。"
                "支持智能过滤：通过 min_importance 参数控制展开节点的最小重要度（默认50）。"
                "数据量可能较大，适合 Agent 分析生成时序图或提取核心逻辑。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "method_id": {
                        "type": "string",
                        "description": "方法的完整ID（如 com.example.UserService.login）"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "展开深度（默认3层，最大10层）",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    },
                    "branches": {
                        "type": "object",
                        "description": "分支选择（可选）：{'抽象方法ID': '实现类ID'}",
                        "additionalProperties": {"type": "string"}
                    },
                    "min_importance": {
                        "type": "integer",
                        "description": "最小重要度阈值（默认50）。低于此值的节点不展开，仅显示节点信息",
                        "default": 50,
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["method_id"]
            }
        ),
        Tool(
            name="search_code",
            description=(
                "【辅助工具】搜索 Java 类或方法。用于查找方法ID供 get_call_sequence 使用。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "node_type": {
                        "type": "string",
                        "enum": ["class", "method", "field", "interface", "enum"],
                        "description": "类型过滤（可选）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量（默认20）",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_method_code",
            description=(
                "【辅助工具】获取方法源代码。用于查看具体实现细节。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "method_id": {
                        "type": "string",
                        "description": "方法的完整ID"
                    }
                },
                "required": ["method_id"]
            }
        ),
        Tool(
            name="get_caller_sequence",
            description=(
                "【核心工具】获取方法的调用者时序图（树形结构，自下而上）。"
                "返回完整的调用链路，展示哪些方法调用了目标方法。"
                "支持接口多实现、覆写关系(OVERRIDES)、虚拟调用边。"
                "支持智能过滤：通过 min_importance 参数控制展开节点的最小重要度（默认50）。"
                "数据量可能较大，适合 Agent 分析生成反向调用链或影响分析。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "method_id": {
                        "type": "string",
                        "description": "方法的完整ID（如 com.example.UserService.login）"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "展开深度（默认3层，最大10层）",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    },
                    "min_importance": {
                        "type": "integer",
                        "description": "最小重要度阈值（默认50）。低于此值的节点不展开，仅显示节点信息",
                        "default": 50,
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["method_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """处理工具调用"""
    start_time = time.time()
    logger.info(f"收到工具调用: {name}, 参数: {json.dumps(arguments, ensure_ascii=False)}")

    storage = get_storage()

    try:
        result = None
        if name == "get_call_sequence":
            result = await handle_get_call_sequence(storage, arguments)
        elif name == "get_caller_sequence":
            result = await handle_get_caller_sequence(storage, arguments)
        elif name == "search_code":
            result = await handle_search_code(storage, arguments)
        elif name == "get_method_code":
            result = await handle_get_method_code(storage, arguments)
        else:
            logger.warning(f"未知工具: {name}")
            result = [TextContent(type="text", text=f"未知工具: {name}")]

        elapsed = time.time() - start_time
        logger.info(f"工具 {name} 执行完成，耗时: {elapsed:.3f}秒")
        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"工具 {name} 执行失败 (耗时 {elapsed:.3f}秒): {e}", exc_info=True)

        # 友好的错误提示
        error_msg = f"""执行失败: {str(e)}

💡 建议:
1. 检查参数是否正确
2. 确认数据库已正确扫描
3. 运行 'jcgraph diagnose' 查看详细诊断信息
4. 如问题持续，请访问: https://github.com/your-org/jcgraph/issues

错误详情已记录到日志文件。
"""
        return [TextContent(type="text", text=error_msg)]


# ==================== 工具处理函数 ====================

async def handle_get_call_sequence(storage: Storage, args: Dict[str, Any]) -> list[TextContent]:
    """处理 get_call_sequence 工具调用 - 直接调用核心逻辑"""
    from jcgraph.server.sequence_builder import build_call_sequence_tree

    method_id = args["method_id"]
    depth = args.get("depth", 3)
    branches = args.get("branches", {})
    min_importance = args.get("min_importance", 50)

    logger.info(f"获取调用时序: method_id={method_id}, depth={depth}, min_importance={min_importance}")

    # 直接调用核心函数（不需要 try/finally，storage 由外层管理）
    result = build_call_sequence_tree(
        storage=storage,
        node_id=method_id,
        depth=depth,
        branches=branches,
        min_importance=min_importance
    )

    # 返回结构化 JSON
    json_output = json.dumps(result, ensure_ascii=False, indent=2)

    return [
        TextContent(
            type="text",
            text=f"# 方法调用时序图\n\n**方法**: `{result['method']['name']}`\n\n"
                 f"**完整路径**: `{result['method']['full_name']}`\n\n"
                 f"**调用深度**: {depth} 层\n\n"
                 f"**调用节点数**: {len(result.get('calls', []))} 个\n\n"
                 f"**分支点数**: {len(result.get('branch_points', []))} 个\n\n"
                 f"## 结构化数据\n\n```json\n{json_output}\n```\n\n"
                 f"**说明**: Agent 可以解析此 JSON 生成时序图或提取核心逻辑。"
        )
    ]


async def handle_get_caller_sequence(storage: Storage, args: Dict[str, Any]) -> list[TextContent]:
    """处理 get_caller_sequence 工具调用 - 获取调用者时序图"""
    from jcgraph.server.sequence_builder import build_caller_sequence_tree

    method_id = args["method_id"]
    depth = args.get("depth", 3)
    min_importance = args.get("min_importance", 50)

    logger.info(f"获取调用者时序: method_id={method_id}, depth={depth}, min_importance={min_importance}")

    # 调用核心函数
    result = build_caller_sequence_tree(
        storage=storage,
        node_id=method_id,
        depth=depth,
        min_importance=min_importance
    )

    # 返回结构化 JSON
    json_output = json.dumps(result, ensure_ascii=False, indent=2)

    return [
        TextContent(
            type="text",
            text=f"# 方法调用者时序图（反向调用链）\n\n**方法**: `{result['method']['name']}`\n\n"
                 f"**完整路径**: `{result['method']['full_name']}`\n\n"
                 f"**调用深度**: {depth} 层\n\n"
                 f"**调用者节点数**: {len(result.get('callers', []))} 个\n\n"
                 f"## 结构化数据\n\n```json\n{json_output}\n```\n\n"
                 f"**说明**: Agent 可以解析此 JSON 生成反向调用链或影响分析图。展示了哪些方法调用了目标方法。"
        )
    ]


async def handle_search_code(storage: Storage, args: Dict[str, Any]) -> list[TextContent]:
    """处理 search_code 工具调用"""
    query = args["query"]
    node_type = args.get("node_type")
    limit = args.get("limit", 20)

    logger.info(f"搜索代码: query={query}, type={node_type}, limit={limit}")

    # 获取项目
    projects = storage.list_projects()
    if not projects:
        return [TextContent(type="text", text="未找到项目，请先扫描 Java 代码")]

    project_id = projects[0]['id']
    cursor = storage.conn.cursor()

    # 搜索
    if node_type:
        cursor.execute(
            """
            SELECT id, type, name, full_name, class_name, file_path, line_start, signature
            FROM nodes
            WHERE project_id = ? AND type = ? AND (name LIKE ? OR full_name LIKE ?)
            LIMIT ?
            """,
            (project_id, node_type, f"%{query}%", f"%{query}%", limit)
        )
    else:
        cursor.execute(
            """
            SELECT id, type, name, full_name, class_name, file_path, line_start, signature
            FROM nodes
            WHERE project_id = ? AND (name LIKE ? OR full_name LIKE ?)
            LIMIT ?
            """,
            (project_id, f"%{query}%", f"%{query}%", limit)
        )

    results = [dict(row) for row in cursor.fetchall()]

    if not results:
        return [TextContent(type="text", text=f"未找到 '{query}'")]

    # 简洁输出 + JSON
    output_lines = [f"找到 {len(results)} 个结果:\n"]
    for item in results:
        output_lines.append(f"- `{item['full_name']}` ({item['type']})")
        if item.get('file_path'):
            output_lines.append(f"  {item['file_path']}:{item.get('line_start', '?')}")

    json_output = json.dumps(results, ensure_ascii=False, indent=2)
    output_lines.append(f"\n```json\n{json_output}\n```")

    return [TextContent(type="text", text="\n".join(output_lines))]


async def handle_get_method_code(storage: Storage, args: Dict[str, Any]) -> list[TextContent]:
    """处理 get_method_code 工具调用"""
    method_id = args["method_id"]

    logger.info(f"获取方法代码: method_id={method_id}")

    # 获取方法信息
    method = storage.get_node(method_id)
    if not method:
        return [TextContent(type="text", text=f"未找到方法: {method_id}")]

    # 获取代码
    code = storage.get_code(method_id)
    if not code:
        return [TextContent(type="text", text=f"方法无源代码: {method_id}")]

    # 返回
    return [
        TextContent(
            type="text",
            text=f"# {method['name']}\n\n"
                 f"**签名**: `{method.get('signature', 'N/A')}`\n\n"
                 f"**文件**: {method.get('file_path', 'N/A')}:{method.get('line_start', '?')}-{method.get('line_end', '?')}\n\n"
                 f"```java\n{code}\n```"
        )
    ]


def main():
    """主函数 - 启动 MCP Server"""
    logger.info("启动 jcgraph MCP Server")

    # 检查数据库
    db_path = find_database()
    if db_path:
        logger.info(f"发现数据库: {db_path}")
    else:
        logger.warning("未发现数据库，将使用默认路径")

    # 运行 MCP Server（通过 stdio）
    import asyncio
    from mcp.server.stdio import stdio_server

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(run())


if __name__ == "__main__":
    main()
