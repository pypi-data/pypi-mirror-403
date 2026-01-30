"""SQLite数据库存储"""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List, Dict


class Storage:
    """SQLite存储管理"""

    def __init__(self, db_path: Union[Path, str]):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # 返回字典格式
        self._init_schema()

    def _init_schema(self):
        """初始化数据库表结构"""
        cursor = self.conn.cursor()

        # 项目表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """)

        # 节点表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                type TEXT NOT NULL,
                subtype TEXT,
                name TEXT NOT NULL,
                full_name TEXT,

                parent_id TEXT,
                package_name TEXT,
                class_name TEXT,

                file_path TEXT,
                line_start INTEGER,
                line_end INTEGER,

                visibility TEXT,
                annotations TEXT,
                signature TEXT,
                return_type TEXT,
                params TEXT,

                comment TEXT,
                summary TEXT,

                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # 代码内容表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_contents (
                node_id TEXT PRIMARY KEY,
                code TEXT,
                FOREIGN KEY (node_id) REFERENCES nodes(id)
            )
        """)

        # 关系/边表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_id TEXT,
                target_raw TEXT,
                relation_type TEXT NOT NULL,
                line_number INTEGER,
                resolved INTEGER DEFAULT 0,
                branch_label TEXT,
                loop_type TEXT,
                loop_id TEXT,
                is_interface_call INTEGER DEFAULT 0,
                lambda_depth INTEGER DEFAULT 0,
                branch_type TEXT,
                branch_id TEXT,
                branch_condition TEXT,
                branch_order INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (source_id) REFERENCES nodes(id)
            )
        """)

        # 检查并添加subtype字段（迁移已有数据库）
        cursor.execute("PRAGMA table_info(nodes)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'subtype' not in columns:
            cursor.execute("ALTER TABLE nodes ADD COLUMN subtype TEXT")
        if 'params' not in columns:
            cursor.execute("ALTER TABLE nodes ADD COLUMN params TEXT")

        # 检查并添加edges新字段（迁移已有数据库）
        cursor.execute("PRAGMA table_info(edges)")
        edge_columns = [row[1] for row in cursor.fetchall()]
        if 'branch_label' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN branch_label TEXT")
        if 'loop_type' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN loop_type TEXT")
        if 'loop_id' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN loop_id TEXT")
        if 'is_interface_call' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN is_interface_call INTEGER DEFAULT 0")
        if 'lambda_depth' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN lambda_depth INTEGER DEFAULT 0")
        # 分支相关字段
        if 'branch_type' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN branch_type TEXT")
        if 'branch_id' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN branch_id TEXT")
        if 'branch_condition' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN branch_condition TEXT")
        if 'branch_order' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN branch_order INTEGER DEFAULT 0")

        # 虚拟调用相关字段（用于接口调用桥接）
        if 'is_virtual' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN is_virtual INTEGER DEFAULT 0")
        if 'actual_target_id' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN actual_target_id TEXT")
        if 'via_interface_id' not in edge_columns:
            cursor.execute("ALTER TABLE edges ADD COLUMN via_interface_id TEXT")

        # 创建索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_nodes_project ON nodes(project_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_nodes_subtype ON nodes(subtype)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_nodes_class ON nodes(class_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_id)"
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_project ON edges(project_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(relation_type)"
        )
        # 虚拟调用索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_actual_target ON edges(actual_target_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_virtual ON edges(is_virtual, source_id)"
        )

        # 创建唯一索引防止重复边
        # 注意：为了支持虚拟调用边,唯一索引需要包含 target_id
        # 先检查旧索引是否存在,如果存在则删除
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name='idx_edges_unique'
        """)
        if cursor.fetchone():
            # 旧索引存在,删除它
            cursor.execute("DROP INDEX IF EXISTS idx_edges_unique")

        # 创建新的唯一索引,包含 target_id
        cursor.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_unique_v2
               ON edges(project_id, source_id, target_id, target_raw, line_number)"""
        )

        self.conn.commit()

    # ==================== 项目管理 ====================

    def create_project(self, name: str, path: str) -> str:
        """创建项目"""
        project_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (id, name, path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, name, path, datetime.now(), datetime.now())
        )
        self.conn.commit()
        return project_id

    def get_project(self, project_id: str) -> Optional[dict]:
        """获取项目信息"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_project_by_path(self, path: str) -> Optional[dict]:
        """根据路径获取项目"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM projects WHERE path = ?",
            (path,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_projects(self) -> List[Dict]:
        """列出所有项目"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_project_timestamp(self, project_id: str):
        """更新项目时间戳"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (datetime.now(), project_id)
        )
        self.conn.commit()

    # ==================== 节点管理 ====================

    def save_node(self, node: dict) -> None:
        """保存单个节点"""
        # 处理注解（转为JSON）
        annotations = node.get('annotations', [])
        if isinstance(annotations, list):
            annotations = json.dumps(annotations)

        # 处理参数（转为JSON）
        params = node.get('params', [])
        if isinstance(params, list):
            params = json.dumps(params)

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO nodes (
                id, project_id, type, subtype, name, full_name,
                parent_id, package_name, class_name,
                file_path, line_start, line_end,
                visibility, annotations, signature, return_type,
                comment, summary, params
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node.get('id'),
                node.get('project_id'),
                node.get('type'),
                node.get('subtype'),
                node.get('name'),
                node.get('full_name'),
                node.get('parent_id'),
                node.get('package_name'),
                node.get('class_name'),
                node.get('file_path'),
                node.get('line_start'),
                node.get('line_end'),
                node.get('visibility'),
                annotations,
                node.get('signature'),
                node.get('return_type'),
                node.get('comment'),
                node.get('summary'),
                params
            )
        )
        self.conn.commit()

    def save_nodes_batch(self, nodes: List[Dict]) -> None:
        """批量保存节点"""
        for node in nodes:
            self.save_node(node)

    def get_node(self, node_id: str) -> Optional[dict]:
        """获取节点信息"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM nodes WHERE id = ?",
            (node_id,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # 解析注解JSON
            if result.get('annotations'):
                result['annotations'] = json.loads(result['annotations'])
            # 解析参数JSON
            if result.get('params'):
                result['params'] = json.loads(result['params'])
            return result
        return None

    def list_nodes(
        self,
        project_id: str,
        node_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """列出节点"""
        cursor = self.conn.cursor()

        query = "SELECT * FROM nodes WHERE project_id = ?"
        params = [project_id]

        if node_type:
            query += " AND type = ?"
            params.append(node_type)

        if parent_id:
            query += " AND parent_id = ?"
            params.append(parent_id)

        query += " LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            # 解析注解JSON
            if result.get('annotations'):
                result['annotations'] = json.loads(result['annotations'])
            # 解析参数JSON
            if result.get('params'):
                result['params'] = json.loads(result['params'])
            results.append(result)
        return results

    # ==================== 代码管理 ====================

    def save_code(self, node_id: str, code: str) -> None:
        """保存代码内容"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO code_contents (node_id, code)
            VALUES (?, ?)
            """,
            (node_id, code)
        )
        self.conn.commit()

    def get_code(self, node_id: str) -> Optional[str]:
        """获取代码内容"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT code FROM code_contents WHERE node_id = ?",
            (node_id,)
        )
        row = cursor.fetchone()
        return row['code'] if row else None

    # ==================== 统计 ====================

    def get_stats(self, project_id: str) -> dict:
        """获取项目统计信息"""
        cursor = self.conn.cursor()

        # 总节点数
        cursor.execute(
            "SELECT COUNT(*) as count FROM nodes WHERE project_id = ?",
            (project_id,)
        )
        total_nodes = cursor.fetchone()['count']

        # 按类型统计
        cursor.execute(
            """
            SELECT type, COUNT(*) as count
            FROM nodes
            WHERE project_id = ?
            GROUP BY type
            """,
            (project_id,)
        )
        by_type = {row['type']: row['count'] for row in cursor.fetchall()}

        # 文件数
        cursor.execute(
            """
            SELECT COUNT(DISTINCT file_path) as count
            FROM nodes
            WHERE project_id = ?
            """,
            (project_id,)
        )
        file_count = cursor.fetchone()['count']

        # 包数
        cursor.execute(
            """
            SELECT COUNT(DISTINCT package_name) as count
            FROM nodes
            WHERE project_id = ? AND package_name IS NOT NULL
            """,
            (project_id,)
        )
        package_count = cursor.fetchone()['count']

        # 边统计
        cursor.execute(
            "SELECT COUNT(*) as count FROM edges WHERE project_id = ?",
            (project_id,)
        )
        edge_count = cursor.fetchone()['count']

        # 按关系类型统计
        cursor.execute(
            """
            SELECT relation_type, COUNT(*) as count
            FROM edges
            WHERE project_id = ?
            GROUP BY relation_type
            """,
            (project_id,)
        )
        by_relation = {row['relation_type']: row['count'] for row in cursor.fetchall()}

        # 未解析的边
        cursor.execute(
            "SELECT COUNT(*) as count FROM edges WHERE project_id = ? AND resolved = 0",
            (project_id,)
        )
        unresolved_count = cursor.fetchone()['count']

        return {
            'total_nodes': total_nodes,
            'file_count': file_count,
            'package_count': package_count,
            'class_count': by_type.get('class', 0) + by_type.get('interface', 0) + by_type.get('enum', 0),
            'method_count': by_type.get('method', 0),
            'field_count': by_type.get('field', 0),
            'by_type': by_type,
            # 边统计
            'edge_count': edge_count,
            'calls': by_relation.get('CALLS', 0),
            'implements': by_relation.get('IMPLEMENTS', 0),
            'extends': by_relation.get('EXTENDS', 0),
            'injects': by_relation.get('INJECTS', 0),
            'unresolved': unresolved_count,
            'by_relation': by_relation
        }

    # ==================== 边/关系管理 ====================

    def save_edge(self, edge: Dict) -> int:
        """
        保存单条边,使用INSERT OR IGNORE防止重复

        唯一索引基于 (project_id, source_id, target_id, target_raw, line_number)
        虚拟边与原始接口调用有不同的 target_id,因此不会冲突
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO edges (
                project_id, source_id, target_id, target_raw,
                relation_type, line_number, resolved, branch_label,
                loop_type, loop_id, is_interface_call, lambda_depth,
                branch_type, branch_id, branch_condition, branch_order,
                is_virtual, actual_target_id, via_interface_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edge.get('project_id'),
                edge.get('source_id'),
                edge.get('target_id'),
                edge.get('target_raw'),
                edge.get('relation_type'),
                edge.get('line_number'),
                1 if edge.get('target_id') else 0,
                edge.get('branch_label'),
                edge.get('loop_type'),
                edge.get('loop_id'),
                edge.get('is_interface_call', 0),
                edge.get('lambda_depth', 0),
                edge.get('branch_type'),
                edge.get('branch_id'),
                edge.get('branch_condition'),
                edge.get('branch_order', 0),
                edge.get('is_virtual', 0),
                edge.get('actual_target_id'),
                edge.get('via_interface_id')
            )
        )
        self.conn.commit()
        return cursor.lastrowid

    def save_edges_batch(self, edges: List[Dict]) -> None:
        """批量保存边"""
        for edge in edges:
            self.save_edge(edge)

    def get_edges_from(self, node_id: str) -> List[Dict]:
        """获取出边：我调用了谁"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM edges WHERE source_id = ?",
            (node_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_edges_to(self, node_id: str) -> List[Dict]:
        """
        获取入边：谁调用了我

        支持虚拟调用边：
        - 查找 target_id = node_id 的直接调用
        - 查找 actual_target_id = node_id 的虚拟调用（通过接口调用实现方法）
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM edges
            WHERE target_id = ? OR actual_target_id = ?
            """,
            (node_id, node_id)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_edges_by_type(self, project_id: str, relation_type: str) -> List[Dict]:
        """按类型获取边"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM edges WHERE project_id = ? AND relation_type = ?",
            (project_id, relation_type)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_callees(self, node_id: str, depth: int = 1) -> List[Dict]:
        """向下追踪：递归查找被调用的方法"""
        visited = set()
        result = []

        def _traverse(nid: str, current_depth: int):
            if current_depth > depth or nid in visited:
                return
            visited.add(nid)

            edges = self.get_edges_from(nid)
            for edge in edges:
                if edge['target_id']:
                    result.append(edge)
                    _traverse(edge['target_id'], current_depth + 1)

        _traverse(node_id, 0)
        return result

    def get_callers(self, node_id: str, depth: int = 1) -> List[Dict]:
        """向上追踪：递归查找调用者"""
        visited = set()
        result = []

        def _traverse(nid: str, current_depth: int):
            if current_depth > depth or nid in visited:
                return
            visited.add(nid)

            edges = self.get_edges_to(nid)
            for edge in edges:
                result.append(edge)
                _traverse(edge['source_id'], current_depth + 1)

        _traverse(node_id, 0)
        return result

    def calculate_call_statistics(self, project_id: str) -> Dict[str, Dict[str, int]]:
        """
        计算所有方法的入度和出度

        Returns:
            {
                "method_id_1": {"in_degree": 5, "out_degree": 3},
                "method_id_2": {"in_degree": 0, "out_degree": 8},
                ...
            }
        """
        cursor = self.conn.cursor()
        stats = {}

        # 入度统计 (被调用次数)
        cursor.execute(
            """
            SELECT target_id, COUNT(*) as cnt
            FROM edges
            WHERE project_id = ? AND relation_type = 'CALLS' AND resolved = 1
            GROUP BY target_id
            """,
            (project_id,)
        )
        for row in cursor.fetchall():
            method_id = row['target_id']
            if method_id not in stats:
                stats[method_id] = {"in_degree": 0, "out_degree": 0}
            stats[method_id]['in_degree'] = row['cnt']

        # 出度统计 (调用其他方法数)
        cursor.execute(
            """
            SELECT source_id, COUNT(*) as cnt
            FROM edges
            WHERE project_id = ? AND relation_type = 'CALLS'
            GROUP BY source_id
            """,
            (project_id,)
        )
        for row in cursor.fetchall():
            method_id = row['source_id']
            if method_id not in stats:
                stats[method_id] = {"in_degree": 0, "out_degree": 0}
            stats[method_id]['out_degree'] = row['cnt']

        return stats

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
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                e.source_id as id,
                n.class_name,
                e.branch_label
            FROM edges e
            JOIN nodes n ON e.source_id = n.id
            WHERE e.target_id = ?
            AND e.relation_type = 'OVERRIDES'
            ORDER BY e.branch_label
            """,
            (method_id,)
        )
        results = [dict(row) for row in cursor.fetchall()]

        # 去重
        seen = set()
        unique = []
        for impl in results:
            if impl['id'] not in seen:
                seen.add(impl['id'])
                unique.append(impl)

        return unique

    def resolve_type(self, project_id: str, type_name: str) -> List[Dict]:
        """
        类型名解析：根据简单类名查找完整的类

        Args:
            project_id: 项目ID
            type_name: 类型名（可能是简单名，如 ProductDetailRequestParam）

        Returns:
            匹配的类列表，按最相似度排序
        """
        cursor = self.conn.cursor()

        # 如果已经是完整名称，直接查询
        if '.' in type_name:
            cursor.execute(
                """
                SELECT * FROM nodes
                WHERE project_id = ? AND type IN ('class', 'interface', 'enum')
                AND (full_name = ? OR name = ?)
                """,
                (project_id, type_name, type_name)
            )
        else:
            # 模糊匹配：name 结尾匹配
            cursor.execute(
                """
                SELECT * FROM nodes
                WHERE project_id = ? AND type IN ('class', 'interface', 'enum')
                AND name = ?
                """,
                (project_id, type_name)
            )

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            # 解析注解JSON
            if result.get('annotations'):
                result['annotations'] = json.loads(result['annotations'])
            results.append(result)

        return results

    def get_class_fields(self, class_id: str) -> List[Dict]:
        """
        获取类的所有字段

        Args:
            class_id: 类的完整名称（如 com.example.MyClass）

        Returns:
            字段列表
        """
        # 提取简单类名（字段的 parent_id 存储的是简单类名）
        simple_name = class_id.split('.')[-1] if '.' in class_id else class_id

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM nodes
            WHERE type = 'field' AND parent_id = ?
            ORDER BY line_start
            """,
            (simple_name,)
        )

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            # 解析注解JSON
            if result.get('annotations'):
                result['annotations'] = json.loads(result['annotations'])
            results.append(result)

        return results

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
