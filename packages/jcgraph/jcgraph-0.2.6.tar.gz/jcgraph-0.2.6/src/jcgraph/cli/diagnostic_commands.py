"""诊断工具命令"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from jcgraph.utils.db_finder import find_database
from jcgraph.storage.sqlite import Storage

console = Console()


@click.group(name="check")
def check_group():
    """诊断和检查命令"""
    pass


@click.command(name="stats")
def stats():
    """显示数据库统计信息"""
    db_path = find_database()
    if not db_path:
        console.print("[red]✗ 未找到数据库，请先运行 jcgraph scan[/red]")
        return

    console.print(f"[cyan]数据库: {db_path}[/cyan]\n")

    storage = Storage(db_path)
    try:
        cursor = storage.conn.cursor()

        # 项目统计
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]

        # 节点类型统计
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM nodes
            GROUP BY type
            ORDER BY count DESC
        """)
        node_stats = cursor.fetchall()

        # 关系统计
        cursor.execute("SELECT COUNT(*) FROM edges")
        edge_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM edges WHERE resolved = 1")
        resolved_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM edges WHERE resolved = 0")
        unresolved_count = cursor.fetchone()[0]

        # 显示统计表格
        table = Table(title="数据库统计")
        table.add_column("类别", style="cyan")
        table.add_column("数量", style="green", justify="right")

        table.add_row("项目", str(project_count))
        table.add_row("", "")

        for node_type, count in node_stats:
            icon = {"class": "📦", "method": "🔧", "field": "📋", "interface": "🔌", "enum": "🏷️"}.get(node_type, "📄")
            table.add_row(f"{icon} {node_type}", str(count))

        table.add_row("", "")
        table.add_row("总边（调用关系）", str(edge_count))
        table.add_row("  └ 已解析", str(resolved_count))
        table.add_row("  └ 未解析", str(unresolved_count))

        console.print(table)

        # 解析率
        if edge_count > 0:
            resolution_rate = (resolved_count / edge_count) * 100
            console.print(f"\n[bold]解析率: {resolution_rate:.1f}%[/bold]")

    finally:
        storage.close()


@check_group.command(name="class")
@click.argument("class_name")
def check_class(class_name: str):
    """检查类是否存在并显示其信息"""
    db_path = find_database()
    if not db_path:
        console.print("[red]✗ 未找到数据库[/red]")
        return

    storage = Storage(db_path)
    try:
        cursor = storage.conn.cursor()

        # 搜索类
        cursor.execute("""
            SELECT id, name, full_name, type, file_path, line_start, line_end
            FROM nodes
            WHERE type IN ('class', 'interface', 'enum')
            AND (name LIKE ? OR full_name LIKE ?)
        """, (f"%{class_name}%", f"%{class_name}%"))

        results = cursor.fetchall()

        if not results:
            console.print(f"[yellow]未找到类: {class_name}[/yellow]")
            return

        console.print(f"[green]找到 {len(results)} 个匹配的类:[/green]\n")

        for row in results:
            row_dict = dict(row)
            type_icon = {"class": "📦", "interface": "🔌", "enum": "🏷️"}.get(row_dict['type'], "📄")

            # 显示类信息
            tree = Tree(f"{type_icon} {row_dict['name']}")
            tree.add(f"完整名称: [cyan]{row_dict['full_name']}[/cyan]")
            tree.add(f"类型: {row_dict['type']}")
            if row_dict['file_path']:
                tree.add(f"文件: {row_dict['file_path']}:{row_dict['line_start']}")

            # 获取字段
            fields = storage.get_class_fields(row_dict['id'])
            if fields:
                fields_node = tree.add(f"字段 ({len(fields)})")
                for field in fields[:5]:  # 最多显示5个
                    fields_node.add(f"{field.get('visibility', '')} {field.get('return_type', '')} {field['name']}")
                if len(fields) > 5:
                    fields_node.add(f"... 还有 {len(fields) - 5} 个字段")

            # 获取方法
            cursor.execute("""
                SELECT name, signature, visibility
                FROM nodes
                WHERE type = 'method' AND parent_id = ?
                LIMIT 6
            """, (row_dict['name'],))
            methods = cursor.fetchall()
            if methods:
                methods_node = tree.add(f"方法 ({len(methods)})")
                for method in methods[:5]:
                    method_dict = dict(method)
                    methods_node.add(f"{method_dict.get('visibility', '')} {method_dict.get('signature', method_dict['name'])}")
                if len(methods) > 5:
                    methods_node.add("...")

            console.print(tree)
            console.print()

    finally:
        storage.close()


@check_group.command(name="method")
@click.argument("method_name")
@click.option("--show-calls", is_flag=True, help="显示调用关系")
def check_method(method_name: str, show_calls: bool):
    """检查方法是否存在并显示调用链"""
    db_path = find_database()
    if not db_path:
        console.print("[red]✗ 未找到数据库[/red]")
        return

    storage = Storage(db_path)
    try:
        cursor = storage.conn.cursor()

        # 搜索方法
        cursor.execute("""
            SELECT id, name, full_name, class_name, signature, return_type, file_path, line_start
            FROM nodes
            WHERE type = 'method'
            AND (name LIKE ? OR full_name LIKE ?)
            LIMIT 10
        """, (f"%{method_name}%", f"%{method_name}%"))

        results = cursor.fetchall()

        if not results:
            console.print(f"[yellow]未找到方法: {method_name}[/yellow]")
            return

        console.print(f"[green]找到 {len(results)} 个匹配的方法:[/green]\n")

        for row in results:
            row_dict = dict(row)

            panel_content = []
            panel_content.append(f"[bold]名称:[/bold] {row_dict['name']}")
            if row_dict.get('full_name'):
                panel_content.append(f"[bold]完整名称:[/bold] {row_dict['full_name']}")
            if row_dict.get('class_name'):
                panel_content.append(f"[bold]所属类:[/bold] {row_dict['class_name']}")
            if row_dict.get('signature'):
                panel_content.append(f"[bold]签名:[/bold] {row_dict['signature']}")
            if row_dict.get('file_path'):
                panel_content.append(f"[bold]文件:[/bold] {row_dict['file_path']}:{row_dict.get('line_start', '?')}")

            console.print(Panel("\n".join(panel_content), title="🔧 方法信息", border_style="cyan"))

            if show_calls:
                # 显示调用关系
                callees = storage.get_callees(row_dict['id'], depth=2)
                callers = storage.get_callers(row_dict['id'], depth=2)

                console.print(f"\n  [bold]被调用方 (它调用了):[/bold] {len(callees)} 个")
                console.print(f"  [bold]调用者 (谁调用了它):[/bold] {len(callers)} 个")

            console.print()

    finally:
        storage.close()


@check_group.command(name="unresolved")
@click.option("--limit", default=20, help="显示数量限制")
def check_unresolved(limit: int):
    """查看未解析的调用"""
    db_path = find_database()
    if not db_path:
        console.print("[red]✗ 未找到数据库[/red]")
        return

    storage = Storage(db_path)
    try:
        cursor = storage.conn.cursor()

        cursor.execute("""
            SELECT source_id, target_raw, line_number, COUNT(*) as count
            FROM edges
            WHERE resolved = 0
            GROUP BY source_id, target_raw
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))

        results = cursor.fetchall()

        if not results:
            console.print("[green]✓ 所有调用都已解析[/green]")
            return

        console.print(f"[yellow]未解析的调用 (前 {limit} 个):[/yellow]\n")

        table = Table()
        table.add_column("来源方法", style="cyan")
        table.add_column("目标（未解析）", style="yellow")
        table.add_column("行号", justify="right")
        table.add_column("次数", justify="right", style="red")

        for row in results:
            row_dict = dict(row)

            # 获取源方法名
            source_node = storage.get_node(row_dict['source_id'])
            source_name = source_node['name'] if source_node else row_dict['source_id']

            table.add_row(
                source_name,
                row_dict['target_raw'],
                str(row_dict.get('line_number', '?')),
                str(row_dict['count'])
            )

        console.print(table)

    finally:
        storage.close()
