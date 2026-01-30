"""CLI入口"""
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()
GLOBAL_DIR = Path.home() / ".jcgraph"
LOCAL_DIR = Path(".jcgraph")

def get_data_dir(local=False):
    if local or LOCAL_DIR.exists():
        return LOCAL_DIR
    return GLOBAL_DIR

@click.group()
@click.version_option()
def app():
    """jcgraph - Java代码知识图谱构建工具"""
    pass

@app.command()
@click.option("--local", is_flag=True, help="项目级初始化")
def init(local):
    """初始化"""
    data_dir = LOCAL_DIR if local else GLOBAL_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "config.yaml").write_text("# jcgraph config\n")
    console.print(f"[green]✓ 初始化完成: {data_dir}[/green]")

@app.command()
@click.argument("path", default=".")
@click.option("--name", default=None, help="项目名称")
@click.option("--no-relations", is_flag=True, help="跳过关系分析")
def scan(path, name, no_relations):
    """扫描Java项目"""
    from jcgraph.scanner.file_scanner import scan_java_files, scan_summary
    from jcgraph.scanner.java_parser import JavaParser
    from jcgraph.scanner.relation_builder import RelationBuilder
    from jcgraph.storage.sqlite import Storage

    project_path = Path(path).resolve()
    if not project_path.exists():
        console.print(f"[red]✗ 路径不存在: {project_path}[/red]")
        return

    # 项目名称
    if not name:
        name = project_path.name

    console.print(f"\n[bold]扫描项目:[/bold] {name}")
    console.print(f"[dim]路径: {project_path}[/dim]\n")

    # 1. 扫描文件
    console.print("[cyan]步骤 1/4: 扫描Java文件...[/cyan]")
    try:
        java_files = list(scan_java_files(project_path))
        console.print(f"[green]✓ 找到 {len(java_files)} 个Java文件[/green]\n")
    except Exception as e:
        console.print(f"[red]✗ 扫描失败: {e}[/red]")
        return

    if len(java_files) == 0:
        console.print("[yellow]没有找到Java文件[/yellow]")
        return

    # 2. 解析文件
    console.print("[cyan]步骤 2/4: 解析代码结构...[/cyan]")
    parser = JavaParser()
    parse_results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("解析中...", total=len(java_files))

        for java_file in java_files:
            try:
                result = parser.parse_file(java_file.path)
                parse_results.append(result)
                progress.update(task, advance=1)
            except Exception as e:
                console.print(f"[yellow]⚠ 解析失败 {java_file.relative_path}: {e}[/yellow]")
                progress.update(task, advance=1)

    total_classes = sum(len(r.classes) for r in parse_results)
    total_methods = sum(len(r.methods) for r in parse_results)
    total_fields = sum(len(r.fields) for r in parse_results)

    console.print(f"[green]✓ 解析完成: {total_classes} 个类, {total_methods} 个方法, {total_fields} 个字段[/green]\n")

    # 3. 存入数据库
    console.print("[cyan]步骤 3/4: 存入数据库...[/cyan]")
    db_path = get_data_dir() / "jcgraph.db"
    storage = Storage(db_path)

    try:
        # 检查项目是否已存在
        existing = storage.get_project_by_path(str(project_path))
        if existing:
            project_id = existing['id']
            console.print(f"[yellow]项目已存在，将更新数据[/yellow]")
        else:
            project_id = storage.create_project(name, str(project_path))

        # 保存节点
        nodes_saved = 0
        for result in parse_results:
            # 保存类
            for class_info in result.classes:
                node = {
                    'id': class_info.full_name,
                    'project_id': project_id,
                    'type': class_info.type,
                    'subtype': class_info.type,  # class/interface/enum/abstract
                    'name': class_info.name,
                    'full_name': class_info.full_name,
                    'package_name': class_info.package,
                    'file_path': class_info.file_path,
                    'line_start': class_info.line_start,
                    'line_end': class_info.line_end,
                    'annotations': class_info.annotations,
                    'comment': class_info.comment,
                }
                storage.save_node(node)
                nodes_saved += 1

            # 保存方法
            for method_info in result.methods:
                node = {
                    'id': method_info.full_name,
                    'project_id': project_id,
                    'type': 'method',
                    'subtype': method_info.subtype,  # normal/static/abstract (from parser)
                    'name': method_info.name,
                    'full_name': method_info.full_name,
                    'class_name': method_info.class_name,
                    'parent_id': method_info.class_name,
                    'file_path': result.file_path,
                    'line_start': method_info.line_start,
                    'line_end': method_info.line_end,
                    'visibility': method_info.visibility,
                    'annotations': method_info.annotations,
                    'signature': method_info.signature,
                    'return_type': method_info.return_type,
                    'params': method_info.params,
                    'comment': method_info.comment,
                }
                storage.save_node(node)
                storage.save_code(method_info.full_name, method_info.code)
                nodes_saved += 1

            # 保存字段
            for field_info in result.fields:
                node = {
                    'id': f"{field_info.class_name}#{field_info.name}",
                    'project_id': project_id,
                    'type': 'field',
                    'name': field_info.name,
                    'class_name': field_info.class_name,
                    'parent_id': field_info.class_name,
                    'visibility': field_info.visibility,
                    'annotations': field_info.annotations,
                    'return_type': field_info.type,
                }
                storage.save_node(node)
                nodes_saved += 1

        storage.update_project_timestamp(project_id)
        console.print(f"[green]✓ 保存完成: {nodes_saved} 个节点[/green]\n")

        # 4. 分析关系
        if not no_relations:
            console.print("[cyan]步骤 4/4: 分析关系...[/cyan]")
            relation_builder = RelationBuilder(storage, project_id)

            # 构建符号表
            relation_builder.build_symbol_table()

            all_relations = []

            # 按文件组织数据
            for result in parse_results:
                # 分析每个类
                for class_info in result.classes:
                    # 继承/实现关系
                    relations = relation_builder.analyze_class_relations(class_info)
                    all_relations.extend(relations)

                    # 获取该类的字段
                    class_fields = [f for f in result.fields if f.class_name == class_info.name]

                    # 依赖注入关系
                    relations = relation_builder.analyze_field_injections(class_fields, class_info.full_name)
                    all_relations.extend(relations)

                    # 方法调用关系
                    class_methods = [m for m in result.methods if m.class_name == class_info.full_name]
                    for method in class_methods:
                        relations = relation_builder.analyze_method_calls(
                            method, class_info, class_fields, result.imports
                        )
                        all_relations.extend(relations)

            # 保存关系
            if all_relations:
                relation_builder.save_relations(all_relations)
                console.print(f"[green]✓ Phase 1 完成: {len(all_relations)} 条关系[/green]")

                # Phase 2: 解析字段方法调用
                console.print("[cyan]Phase 2: 解析字段方法调用...[/cyan]")
                resolved_count = relation_builder.resolve_field_method_calls()
                console.print(f"[green]✓ Phase 2 完成: 额外解析 {resolved_count} 个方法调用[/green]")

                # Phase 3: 分析覆写关系
                console.print("[cyan]Phase 3: 分析覆写关系...[/cyan]")
                override_count = 0

                for result in parse_results:
                    for class_info in result.classes:
                        # 获取该类的所有方法
                        class_methods = [m for m in result.methods if m.class_name == class_info.full_name]

                        # 分析覆写关系
                        override_relations = relation_builder.analyze_override_relations(
                            class_info,
                            class_methods
                        )

                        # 保存覆写关系（带 branch_label）
                        for relation in override_relations:
                            # 提取分支标识
                            branch_label = relation_builder._extract_branch_label(class_info.name)

                            storage.save_edge({
                                'project_id': project_id,
                                'source_id': relation.source_id,
                                'target_id': relation.target_id,
                                'target_raw': relation.target_raw,
                                'relation_type': 'OVERRIDES',
                                'line_number': relation.line_number,
                                'branch_label': branch_label,
                            })
                            override_count += 1

                console.print(f"[green]✓ Phase 3 完成: {override_count} 个覆写关系[/green]")

                # Phase 4: 生成虚拟调用边
                console.print("[cyan]Phase 4: 生成虚拟调用边...[/cyan]")
                virtual_edges_count = relation_builder.generate_virtual_call_edges()
                console.print(f"[green]✓ Phase 4 完成: {virtual_edges_count} 条虚拟调用边[/green]\n")
            else:
                console.print("[yellow]未发现关系[/yellow]\n")
        else:
            console.print("[yellow]跳过关系分析（使用 --no-relations）[/yellow]\n")

        # 显示统计
        stats = storage.get_stats(project_id)
        table = Table(title="扫描结果统计")
        table.add_column("指标", style="cyan")
        table.add_column("数量", style="green", justify="right")

        table.add_row("文件数", str(stats['file_count']))
        table.add_row("包数", str(stats['package_count']))
        table.add_row("类数", str(stats['class_count']))
        table.add_row("方法数", str(stats['method_count']))
        table.add_row("字段数", str(stats['field_count']))

        if not no_relations:
            table.add_row("─" * 10, "─" * 10)
            table.add_row("调用关系", str(stats.get('calls', 0)))
            table.add_row("继承关系", str(stats.get('extends', 0)))
            table.add_row("实现关系", str(stats.get('implements', 0)))
            table.add_row("注入关系", str(stats.get('injects', 0)))
            table.add_row("总关系数", str(stats.get('edge_count', 0)))

        console.print(table)
        console.print(f"\n[green]✓ 扫描完成！[/green]")
        console.print(f"[dim]数据库: {db_path}[/dim]")
        console.print(f"[dim]使用 [bold]jcgraph serve[/bold] 启动Web查看[/dim]\n")

    except Exception as e:
        console.print(f"[red]✗ 保存失败: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        storage.close()

@app.command()
@click.option("--port", default=8080, help="端口号")
@click.option("--host", default="127.0.0.1", help="监听地址")
def serve(port, host):
    """启动Web服务"""
    import uvicorn
    from jcgraph.server.api import app as fastapi_app

    console.print(f"\n[bold green]jcgraph Web服务启动中...[/bold green]\n")
    console.print(f"[cyan]访问地址:[/cyan] http://{host}:{port}")
    console.print(f"[dim]按 Ctrl+C 停止服务[/dim]\n")

    try:
        uvicorn.run(fastapi_app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        console.print("\n[yellow]服务已停止[/yellow]")

@app.command()
@click.argument("keyword")
def query(keyword):
    """查询"""
    console.print(f"查询: {keyword}")
    console.print("[yellow]开发中...[/yellow]")

@app.command()
@click.argument("method")
@click.option("--depth", default=3)
def trace(method, depth):
    """追踪调用链"""
    console.print(f"追踪: {method}, 深度: {depth}")
    console.print("[yellow]开发中...[/yellow]")


# 注册 MCP 命令组
from jcgraph.cli.mcp_commands import mcp_group
app.add_command(mcp_group)

# 注册诊断命令组
from jcgraph.cli.diagnostic_commands import check_group, stats
from jcgraph.cli.diagnose_command import diagnose
app.add_command(check_group)
app.add_command(stats)
app.add_command(diagnose)


if __name__ == "__main__":
    app()
