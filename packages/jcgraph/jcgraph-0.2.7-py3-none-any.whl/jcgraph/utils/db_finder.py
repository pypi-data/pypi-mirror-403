"""数据库自动检测工具"""
import os
from pathlib import Path
from typing import Optional


def find_database() -> Optional[Path]:
    """
    自动查找 jcgraph 数据库文件

    优先级：
    1. 环境变量 JCGRAPH_DB 指定的路径
    2. 当前目录 .jcgraph/*.db
    3. 全局目录 ~/.jcgraph/*.db（选择最近修改的）

    Returns:
        数据库文件路径，如果找不到则返回 None
    """
    # 1. 环境变量指定
    env_db = os.environ.get('JCGRAPH_DB')
    if env_db:
        db_path = Path(env_db)
        if db_path.exists() and db_path.is_file():
            return db_path

    # 2. 当前目录 .jcgraph/*.db
    local_jcgraph = Path.cwd() / '.jcgraph'
    if local_jcgraph.exists() and local_jcgraph.is_dir():
        db_files = list(local_jcgraph.glob('*.db'))
        if db_files:
            # 返回最近修改的
            return max(db_files, key=lambda p: p.stat().st_mtime)

    # 3. 全局目录 ~/.jcgraph/*.db
    global_jcgraph = Path.home() / '.jcgraph'
    if global_jcgraph.exists() and global_jcgraph.is_dir():
        db_files = list(global_jcgraph.glob('*.db'))
        if db_files:
            # 返回最近修改的
            return max(db_files, key=lambda p: p.stat().st_mtime)

    return None


def get_default_database() -> Path:
    """
    获取默认数据库路径（用于初始化）

    Returns:
        默认数据库路径 ~/.jcgraph/jcgraph.db
    """
    return Path.home() / '.jcgraph' / 'jcgraph.db'
