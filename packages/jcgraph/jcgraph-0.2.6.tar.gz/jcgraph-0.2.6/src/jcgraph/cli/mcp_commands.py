"""MCP Server 相关的 CLI 命令"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


# 各客户端的配置文件路径
CLIENT_CONFIGS = {
    "cursor": Path.home() / ".cursor" / "mcp.json",
    "claude-cli": Path.home() / ".claude" / "mcp_servers.json",
    "claude-desktop": Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
}


def get_jcgraph_mcp_config(python_path: str = "python3") -> Dict[str, Any]:
    """
    生成 jcgraph MCP Server 配置

    Args:
        python_path: Python 解释器路径

    Returns:
        MCP Server 配置字典
    """
    return {
        "command": python_path,
        "args": ["-m", "jcgraph.server.mcp_server"],
        "env": {}
    }


@click.group(name="mcp")
def mcp_group():
    """MCP Server 相关命令"""
    pass


@mcp_group.command(name="setup")
@click.option(
    "--client",
    type=click.Choice(["cursor", "claude-cli", "claude-desktop"], case_sensitive=False),
    required=True,
    help="目标客户端"
)
@click.option(
    "--python",
    default="python3",
    help="Python 解释器路径（需要 3.10+ 且安装了 mcp）"
)
def mcp_setup(client: str, python: str):
    """配置 MCP Server 到指定客户端"""
    config_path = CLIENT_CONFIGS[client]

    # 检查配置文件目录是否存在
    if not config_path.parent.exists():
        console.print(f"[yellow]警告: {client} 配置目录不存在: {config_path.parent}[/yellow]")
        if not click.confirm("是否创建目录?"):
            return
        config_path.parent.mkdir(parents=True, exist_ok=True)

    # 读取现有配置
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            console.print(f"[red]配置文件格式错误: {config_path}[/red]")
            return
    else:
        config = {}

    # 确保有 mcpServers 字段
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # 添加 jcgraph 配置
    jcgraph_config = get_jcgraph_mcp_config(python)
    config["mcpServers"]["jcgraph"] = jcgraph_config

    # 写入配置
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓ 已配置 jcgraph MCP Server 到 {client}[/green]")
        console.print(f"[dim]配置文件: {config_path}[/dim]")
        console.print()
        console.print(Panel.fit(
            f"[yellow]提示[/yellow]\n\n"
            f"1. 确保 Python 版本 >= 3.10\n"
            f"2. 安装 MCP SDK: pip install mcp\n"
            f"3. 重启 {client} 以生效",
            title="下一步",
            border_style="yellow"
        ))
    except Exception as e:
        console.print(f"[red]✗ 写入配置失败: {e}[/red]")


@mcp_group.command(name="status")
def mcp_status():
    """查看 MCP Server 配置状态"""
    table = Table(title="jcgraph MCP Server 配置状态")
    table.add_column("客户端", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("配置文件", style="dim")

    for client_name, config_path in CLIENT_CONFIGS.items():
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                if "mcpServers" in config and "jcgraph" in config["mcpServers"]:
                    status = "✓ 已配置"
                    style = "green"
                else:
                    status = "○ 未配置"
                    style = "yellow"
            except:
                status = "✗ 配置错误"
                style = "red"
        else:
            status = "○ 文件不存在"
            style = "dim"

        table.add_row(client_name, status, str(config_path))

    console.print(table)


@mcp_group.command(name="remove")
@click.option(
    "--client",
    type=click.Choice(["cursor", "claude-cli", "claude-desktop"], case_sensitive=False),
    required=True,
    help="目标客户端"
)
def mcp_remove(client: str):
    """从指定客户端移除 jcgraph MCP Server 配置"""
    config_path = CLIENT_CONFIGS[client]

    if not config_path.exists():
        console.print(f"[yellow]配置文件不存在: {config_path}[/yellow]")
        return

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if "mcpServers" in config and "jcgraph" in config["mcpServers"]:
            del config["mcpServers"]["jcgraph"]

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            console.print(f"[green]✓ 已从 {client} 移除 jcgraph MCP Server[/green]")
        else:
            console.print(f"[yellow]{client} 中未配置 jcgraph MCP Server[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ 操作失败: {e}[/red]")


@mcp_group.command(name="debug")
def mcp_debug():
    """以调试模式启动 MCP Server"""
    import os
    import subprocess

    console.print("[cyan]以调试模式启动 jcgraph MCP Server...[/cyan]")

    env = os.environ.copy()
    env["JCGRAPH_DEBUG"] = "1"

    try:
        subprocess.run(
            [sys.executable, "-m", "jcgraph.server.mcp_server"],
            env=env
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]已停止 MCP Server[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ 启动失败: {e}[/red]")
