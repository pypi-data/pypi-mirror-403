"""FastAPI Web服务"""
from pathlib import Path
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jcgraph.storage.sqlite import Storage
from jcgraph.server.sequence_builder import build_call_sequence_tree, build_caller_sequence_tree, calculate_importance


# Request models
class SequenceRequest(BaseModel):
    branches: Optional[Dict[str, str]] = None
    min_importance: Optional[int] = 50  # 最小重要度阈值，默认50


# 获取数据目录
def get_data_dir() -> Path:
    """获取数据目录"""
    local_dir = Path(".jcgraph")
    if local_dir.exists():
        return local_dir
    return Path.home() / ".jcgraph"


# 创建FastAPI应用
app = FastAPI(title="jcgraph", description="Java代码知识图谱")

# 静态文件
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ==================== 工具函数 ====================

def get_storage() -> Storage:
    """获取数据库连接"""
    db_path = get_data_dir() / "jcgraph.db"
    return Storage(db_path)


# calculate_importance 函数已移至 sequence_builder.py
# 从 jcgraph.server.sequence_builder 导入使用


# ==================== API路由 ====================

@app.get("/")
async def index():
    """首页"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>jcgraph</h1><p>请先扫描项目</p>")


@app.get("/api/projects")
async def list_projects():
    """项目列表"""
    storage = get_storage()
    try:
        projects = storage.list_projects()
        # 为每个项目添加统计信息
        for project in projects:
            project['stats'] = storage.get_stats(project['id'])
        return {"projects": projects}
    finally:
        storage.close()


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """项目详情"""
    storage = get_storage()
    try:
        project = storage.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return project
    finally:
        storage.close()


@app.get("/api/projects/{project_id}/stats")
async def get_project_stats(project_id: str):
    """项目统计信息"""
    storage = get_storage()
    try:
        stats = storage.get_stats(project_id)
        return stats
    finally:
        storage.close()


@app.get("/api/nodes")
async def list_nodes(
    project_id: str,
    type: Optional[str] = None,
    parent_id: Optional[str] = None,
    limit: int = 1000
):
    """节点列表"""
    storage = get_storage()
    try:
        nodes = storage.list_nodes(project_id, type, parent_id, limit)
        return {"nodes": nodes}
    finally:
        storage.close()


@app.get("/api/nodes/{node_id}")
async def get_node(node_id: str):
    """节点详情"""
    storage = get_storage()
    try:
        node = storage.get_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="节点不存在")
        return node
    finally:
        storage.close()


@app.get("/api/nodes/{node_id}/code")
async def get_node_code(node_id: str):
    """获取节点代码"""
    storage = get_storage()
    try:
        code = storage.get_code(node_id)
        if code is None:
            raise HTTPException(status_code=404, detail="代码不存在")
        return {"code": code}
    finally:
        storage.close()


@app.get("/api/classes")
async def list_classes(project_id: str, limit: int = 1000):
    """类列表"""
    storage = get_storage()
    try:
        nodes = storage.list_nodes(project_id, node_type="class", limit=limit)
        # 同时获取interface和enum
        nodes += storage.list_nodes(project_id, node_type="interface", limit=limit)
        nodes += storage.list_nodes(project_id, node_type="enum", limit=limit)
        return {"classes": nodes}
    finally:
        storage.close()


@app.get("/api/classes/{class_id}/methods")
async def get_class_methods(class_id: str):
    """获取类的方法列表"""
    storage = get_storage()
    try:
        # 先获取类信息
        class_node = storage.get_node(class_id)
        if not class_node:
            raise HTTPException(status_code=404, detail="类不存在")

        # 获取类的所有方法
        methods = storage.list_nodes(
            class_node['project_id'],
            node_type="method",
            parent_id=class_id
        )
        return {"methods": methods}
    finally:
        storage.close()


@app.get("/api/classes/{class_id}/fields")
async def get_class_fields(class_id: str):
    """获取类的字段列表"""
    storage = get_storage()
    try:
        # 先获取类信息
        class_node = storage.get_node(class_id)
        if not class_node:
            raise HTTPException(status_code=404, detail="类不存在")

        # 获取类的所有字段
        fields = storage.get_class_fields(class_id)
        return {
            "class": {
                "id": class_node['id'],
                "name": class_node['name'],
                "full_name": class_node.get('full_name'),
                "type": class_node.get('type')
            },
            "fields": fields
        }
    finally:
        storage.close()


@app.get("/api/search")
async def search(q: str, project_id: Optional[str] = None, limit: int = 20):
    """全局搜索类、方法和源代码内容"""
    if not q or len(q) < 2:
        return {"classes": [], "methods": [], "code_refs": []}

    storage = get_storage()
    try:
        cursor = storage.conn.cursor()

        # 如果没有指定项目，使用最新的项目
        if not project_id:
            cursor.execute("SELECT id FROM projects ORDER BY updated_at DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                project_id = row['id']
            else:
                return {"classes": [], "methods": [], "code_refs": []}

        # 搜索类（使用LIKE模糊匹配）
        cursor.execute(
            """
            SELECT * FROM nodes
            WHERE project_id = ?
            AND type IN ('class', 'interface', 'enum')
            AND (name LIKE ? OR full_name LIKE ?)
            ORDER BY name
            LIMIT ?
            """,
            (project_id, f'%{q}%', f'%{q}%', limit)
        )
        classes = [dict(row) for row in cursor.fetchall()]

        # 搜索方法（按名称）
        cursor.execute(
            """
            SELECT * FROM nodes
            WHERE project_id = ?
            AND type = 'method'
            AND (name LIKE ? OR full_name LIKE ?)
            ORDER BY name
            LIMIT ?
            """,
            (project_id, f'%{q}%', f'%{q}%', limit)
        )
        methods = [dict(row) for row in cursor.fetchall()]

        # 搜索源代码内容
        cursor.execute(
            """
            SELECT
                n.id,
                n.name,
                n.class_name,
                n.file_path,
                n.line_start,
                n.line_end,
                c.code
            FROM nodes n
            JOIN code_contents c ON n.id = c.node_id
            WHERE n.project_id = ?
            AND n.type = 'method'
            AND c.code LIKE ?
            ORDER BY n.class_name, n.name
            LIMIT ?
            """,
            (project_id, f'%{q}%', limit)
        )

        code_refs = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            code = row_dict['code']

            # 提取包含关键词的代码行及上下文
            lines = code.split('\n')
            matched_lines = []
            for i, line in enumerate(lines):
                if q.lower() in line.lower():
                    # 记录匹配行号（相对于方法内的行号）
                    matched_lines.append({
                        'line_in_method': i + 1,
                        'absolute_line': row_dict['line_start'] + i,
                        'content': line.strip()
                    })

            if matched_lines:
                code_refs.append({
                    'method_id': row_dict['id'],
                    'method_name': row_dict['name'],
                    'class_name': row_dict['class_name'],
                    'file_path': row_dict['file_path'],
                    'method_start_line': row_dict['line_start'],
                    'method_end_line': row_dict['line_end'],
                    'matched_lines': matched_lines[:3]  # 最多显示3个匹配行
                })

        return {
            "classes": classes,
            "methods": methods,
            "code_refs": code_refs
        }
    finally:
        storage.close()


@app.get("/api/types/resolve")
async def resolve_type(type_name: str, project_id: str):
    """
    类型名解析：根据简单类名或完整类名查找类定义

    Args:
        type_name: 类型名（如 ProductDetailRequestParam 或 com.example.ProductDetailRequestParam）
        project_id: 项目ID

    Returns:
        匹配的类列表
    """
    if not type_name:
        raise HTTPException(status_code=400, detail="type_name 不能为空")

    storage = get_storage()
    try:
        classes = storage.resolve_type(project_id, type_name)
        return {"classes": classes}
    finally:
        storage.close()


@app.get("/api/methods/{method_id}/code")
async def get_method_code(method_id: str):
    """获取方法代码"""
    storage = get_storage()
    try:
        # 获取方法信息
        method = storage.get_node(method_id)
        if not method:
            raise HTTPException(status_code=404, detail="方法不存在")

        # 获取代码
        code = storage.get_code(method_id)

        return {
            "code": code or "",
            "line_start": method.get('line_start', 0),
            "line_end": method.get('line_end', 0),
            "signature": method.get('signature', ''),
            "file_path": method.get('file_path', '')
        }
    finally:
        storage.close()


@app.get("/api/edges")
async def list_edges(
    project_id: Optional[str] = None,
    source_id: Optional[str] = None,
    target_id: Optional[str] = None,
    relation_type: Optional[str] = None
):
    """边/关系查询"""
    storage = get_storage()
    try:
        if source_id:
            # 查询出边：我调用了谁
            edges = storage.get_edges_from(source_id)
        elif target_id:
            # 查询入边：谁调用了我
            edges = storage.get_edges_to(target_id)
        elif project_id and relation_type:
            # 按类型查询
            edges = storage.get_edges_by_type(project_id, relation_type)
        else:
            raise HTTPException(status_code=400, detail="需要提供 source_id, target_id 或 (project_id + relation_type)")

        return {"edges": edges}
    finally:
        storage.close()


@app.get("/api/graph/callees/{node_id}")
async def get_callees(node_id: str, depth: int = 2):
    """向下追踪：我调用了谁（递归）"""
    storage = get_storage()
    try:
        edges = storage.get_callees(node_id, depth)

        # 构建节点列表
        node_ids = {node_id}
        for edge in edges:
            node_ids.add(edge['source_id'])
            if edge['target_id']:
                node_ids.add(edge['target_id'])

        # 获取节点信息
        nodes = []
        for nid in node_ids:
            node = storage.get_node(nid)
            if node:
                nodes.append({
                    'id': node['id'],
                    'name': node['name'],
                    'type': node['type'],
                    'full_name': node.get('full_name', '')
                })

        return {
            "root": node_id,
            "nodes": nodes,
            "edges": edges
        }
    finally:
        storage.close()


@app.get("/api/graph/callers/{node_id}")
async def get_callers(node_id: str, depth: int = 2):
    """向上追踪：谁调用了我（递归）"""
    storage = get_storage()
    try:
        edges = storage.get_callers(node_id, depth)

        # 构建节点列表
        node_ids = {node_id}
        for edge in edges:
            node_ids.add(edge['source_id'])
            if edge['target_id']:
                node_ids.add(edge['target_id'])

        # 获取节点信息
        nodes = []
        for nid in node_ids:
            node = storage.get_node(nid)
            if node:
                nodes.append({
                    'id': node['id'],
                    'name': node['name'],
                    'type': node['type'],
                    'full_name': node.get('full_name', '')
                })

        return {
            "root": node_id,
            "nodes": nodes,
            "edges": edges
        }
    finally:
        storage.close()


# build_call_sequence_tree 函数已移至 sequence_builder.py
# 从 jcgraph.server.sequence_builder 导入使用


# ==================== Web API 包装层 ====================

async def get_call_sequence(node_id: str, request: SequenceRequest, depth: int = 3) -> dict:
    """
    Web API 包装 - 获取调用时序图

    负责：
    - 创建/关闭 Storage
    - 将 ValueError 转换为 HTTPException
    """
    storage = get_storage()
    try:
        return build_call_sequence_tree(
            storage=storage,
            node_id=node_id,
            depth=depth,
            branches=request.branches or {},
            min_importance=request.min_importance if request.min_importance is not None else 50
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        storage.close()


# POST端点（支持分支选择）
@app.post("/api/graph/sequence/{node_id}")
async def get_call_sequence_post(node_id: str, request: SequenceRequest, depth: int = 3):
    """POST请求接口，支持分支选择"""
    return await get_call_sequence(node_id, request, depth)


# 兼容GET请求（无分支选择）
@app.get("/api/graph/sequence/{node_id}")
async def get_call_sequence_get(node_id: str, depth: int = 3, min_importance: int = 50):
    """GET请求兼容性包装"""
    return await get_call_sequence(
        node_id,
        SequenceRequest(branches=None, min_importance=min_importance),
        depth
    )


# ==================== 向上时序图 API ====================

async def get_caller_sequence(node_id: str, request: SequenceRequest, depth: int = 3) -> dict:
    """
    Web API 包装 - 获取向上调用时序图（谁调用了我）

    负责：
    - 创建/关闭 Storage
    - 将 ValueError 转换为 HTTPException
    """
    storage = get_storage()
    try:
        return build_caller_sequence_tree(
            storage=storage,
            node_id=node_id,
            depth=depth,
            branches=request.branches or {},
            min_importance=request.min_importance if request.min_importance is not None else 50
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        storage.close()


# POST端点（支持分支选择）
@app.post("/api/graph/callers-sequence/{node_id}")
async def get_caller_sequence_post(node_id: str, request: SequenceRequest, depth: int = 3):
    """POST请求接口，支持分支选择"""
    return await get_caller_sequence(node_id, request, depth)


# 兼容GET请求（无分支选择）
@app.get("/api/graph/callers-sequence/{node_id}")
async def get_caller_sequence_get(node_id: str, depth: int = 3, min_importance: int = 50):
    """GET请求兼容性包装 - 向上时序图"""
    return await get_caller_sequence(
        node_id,
        SequenceRequest(branches=None, min_importance=min_importance),
        depth
    )


# 健康检查
@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
