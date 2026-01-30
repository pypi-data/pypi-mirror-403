"""诊断导出命令"""
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jcgraph.utils.db_finder import find_database
from jcgraph.utils.logger import get_recent_logs, get_error_logs
from jcgraph.storage.sqlite import Storage

console = Console()


@click.command(name="diagnose")
@click.option("--output", "-o", help="输出文件路径（默认 ~/.jcgraph/diagnose-YYYYMMDD.txt）")
def diagnose(output: str):
    """
    生成诊断信息并导出

    收集 jcgraph 系统信息、数据库统计、错误日志等，
    用于问题排查和反馈。
    """
    console.print("[cyan]正在收集诊断信息...[/cyan]\n")

    # 收集诊断信息
    diag_info = collect_diagnostic_info()

    # 确定输出路径
    if output:
        output_path = Path(output)
    else:
        jcgraph_dir = Path.home() / '.jcgraph'
        jcgraph_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d')
        output_path = jcgraph_dir / f"diagnose-{timestamp}.txt"

    # 写入文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(diag_info)
        console.print(f"[green]✓ 诊断信息已导出到: {output_path}[/green]")
    except Exception as e:
        console.print(f"[red]✗ 导出失败: {e}[/red]")
        return

    # 同时在控制台显示摘要
    display_summary(diag_info)

    # 提示
    console.print()
    console.print(Panel.fit(
        f"[yellow]诊断信息已保存[/yellow]\n\n"
        f"文件路径: {output_path}\n\n"
        f"如需反馈问题，请携带此文件访问:\n"
        f"https://github.com/your-org/jcgraph/issues",
        title="提示",
        border_style="yellow"
    ))


def collect_diagnostic_info() -> str:
    """收集诊断信息"""
    lines = []

    # 标题
    lines.append("=" * 80)
    lines.append("jcgraph 诊断报告")
    lines.append("=" * 80)
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 1. 版本信息
    lines.append("=" * 80)
    lines.append("1. 版本信息")
    lines.append("=" * 80)

    try:
        import jcgraph
        version = getattr(jcgraph, '__version__', '未知')
    except:
        version = '未知'

    lines.append(f"jcgraph 版本: {version}")
    lines.append(f"Python 版本: {sys.version}")
    lines.append(f"Python 路径: {sys.executable}")
    lines.append("")

    # 2. 数据库信息
    lines.append("=" * 80)
    lines.append("2. 数据库信息")
    lines.append("=" * 80)

    db_path = find_database()
    if db_path:
        lines.append(f"数据库路径: {db_path}")
        lines.append(f"数据库大小: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
        lines.append(f"最后修改: {datetime.fromtimestamp(db_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        lines.append("❌ 未找到数据库")
        lines.append("")
        lines.append("建议:")
        lines.append("  - 运行 'jcgraph scan <项目路径>' 扫描 Java 项目")
        lines.append("  - 检查是否在正确的项目目录下")

    lines.append("")

    # 3. 数据统计
    if db_path:
        lines.append("=" * 80)
        lines.append("3. 数据统计")
        lines.append("=" * 80)

        try:
            storage = Storage(db_path)
            cursor = storage.conn.cursor()

            # 项目统计
            cursor.execute("SELECT COUNT(*) FROM projects")
            project_count = cursor.fetchone()[0]
            lines.append(f"项目数量: {project_count}")

            # 节点统计
            cursor.execute("""
                SELECT type, COUNT(*) as count
                FROM nodes
                GROUP BY type
                ORDER BY count DESC
            """)
            lines.append("\n节点统计:")
            for row in cursor.fetchall():
                node_type, count = row
                lines.append(f"  - {node_type}: {count}")

            # 关系统计
            cursor.execute("SELECT COUNT(*) FROM edges")
            edge_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM edges WHERE resolved = 1")
            resolved_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM edges WHERE resolved = 0")
            unresolved_count = cursor.fetchone()[0]

            lines.append(f"\n调用关系:")
            lines.append(f"  - 总数: {edge_count}")
            lines.append(f"  - 已解析: {resolved_count}")
            lines.append(f"  - 未解析: {unresolved_count}")

            if edge_count > 0:
                resolution_rate = (resolved_count / edge_count) * 100
                lines.append(f"  - 解析率: {resolution_rate:.1f}%")

            storage.close()

        except Exception as e:
            lines.append(f"❌ 读取数据库失败: {e}")

        lines.append("")

    # 4. 最近的错误日志
    lines.append("=" * 80)
    lines.append("4. 最近的错误日志 (最多20条)")
    lines.append("=" * 80)

    error_logs = get_error_logs(limit=20)
    if error_logs and "没有发现错误日志" not in error_logs:
        lines.append(error_logs)
    else:
        lines.append("✓ 没有发现错误日志")

    lines.append("")

    # 5. 完整日志（最近50行）
    lines.append("=" * 80)
    lines.append("5. 最近的日志 (最多50行)")
    lines.append("=" * 80)

    recent_logs = get_recent_logs(lines=50)
    lines.append(recent_logs)

    lines.append("")
    lines.append("=" * 80)
    lines.append("诊断报告结束")
    lines.append("=" * 80)

    return '\n'.join(lines)


def display_summary(diag_info: str):
    """在控制台显示摘要"""
    console.print("\n[bold]诊断摘要[/bold]\n")

    # 提取关键信息
    lines = diag_info.split('\n')

    # 版本
    for line in lines:
        if line.startswith("jcgraph 版本:"):
            console.print(f"  {line}")
        elif line.startswith("Python 版本:"):
            console.print(f"  {line.split('(')[0].strip()}")  # 只显示版本号

    # 数据库
    console.print()
    for line in lines:
        if line.startswith("数据库路径:"):
            console.print(f"  {line}")
        elif line.startswith("数据库大小:"):
            console.print(f"  {line}")

    # 统计
    console.print()
    in_stats = False
    for line in lines:
        if line.startswith("3. 数据统计"):
            in_stats = True
            continue
        if in_stats:
            if line.startswith("==="):
                break
            if line.strip() and not line.startswith("项目数量"):
                console.print(f"  {line}")

    # 错误日志
    has_errors = False
    for line in lines:
        if " - ERROR - " in line or " - CRITICAL - " in line:
            has_errors = True
            break

    if has_errors:
        console.print()
        console.print("  [yellow]⚠ 发现错误日志，请查看导出文件了解详情[/yellow]")
    else:
        console.print()
        console.print("  [green]✓ 未发现错误日志[/green]")
