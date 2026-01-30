"""日志记录工具"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "jcgraph",
    log_dir: Optional[Path] = None,
    debug: bool = False
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: Logger 名称
        log_dir: 日志目录，默认 ~/.jcgraph/logs
        debug: 是否启用调试模式

    Returns:
        配置好的 Logger 实例
    """
    # 创建 logger
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 设置日志级别
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)  # 控制台只显示警告和错误
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if log_dir is None:
        log_dir = Path.home() / '.jcgraph' / 'logs'

    log_dir.mkdir(parents=True, exist_ok=True)

    # 按日期命名日志文件
    log_file = log_dir / f"mcp-{datetime.now().strftime('%Y-%m-%d')}.log"

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info(f"日志记录器已初始化，日志文件: {log_file}")

    return logger


def get_logger(name: str = "jcgraph") -> logging.Logger:
    """
    获取已配置的 logger

    Args:
        name: Logger 名称

    Returns:
        Logger 实例
    """
    return logging.getLogger(name)


def get_recent_logs(log_dir: Optional[Path] = None, lines: int = 50) -> str:
    """
    获取最近的日志内容

    Args:
        log_dir: 日志目录
        lines: 读取行数

    Returns:
        日志内容字符串
    """
    if log_dir is None:
        log_dir = Path.home() / '.jcgraph' / 'logs'

    if not log_dir.exists():
        return "日志目录不存在"

    # 获取最新的日志文件
    log_files = sorted(log_dir.glob('mcp-*.log'), key=lambda p: p.stat().st_mtime, reverse=True)

    if not log_files:
        return "没有找到日志文件"

    latest_log = log_files[0]

    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            # 返回最后 N 行
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return ''.join(recent_lines)
    except Exception as e:
        return f"读取日志失败: {e}"


def get_error_logs(log_dir: Optional[Path] = None, limit: int = 20) -> str:
    """
    获取最近的错误日志

    Args:
        log_dir: 日志目录
        limit: 返回条数

    Returns:
        错误日志内容
    """
    if log_dir is None:
        log_dir = Path.home() / '.jcgraph' / 'logs'

    if not log_dir.exists():
        return "日志目录不存在"

    # 获取所有日志文件
    log_files = sorted(log_dir.glob('mcp-*.log'), key=lambda p: p.stat().st_mtime, reverse=True)

    if not log_files:
        return "没有找到日志文件"

    error_lines = []
    for log_file in log_files[:3]:  # 只查看最近3个文件
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if ' - ERROR - ' in line or ' - CRITICAL - ' in line:
                        error_lines.append(line.strip())
                        if len(error_lines) >= limit:
                            break
        except Exception:
            continue

        if len(error_lines) >= limit:
            break

    if not error_lines:
        return "没有发现错误日志"

    return '\n'.join(error_lines)
