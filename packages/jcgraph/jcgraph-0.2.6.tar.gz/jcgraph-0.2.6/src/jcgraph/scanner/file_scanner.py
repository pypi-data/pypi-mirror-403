"""Java文件扫描器"""
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Union, Optional, Set


@dataclass
class JavaFile:
    """Java文件信息"""
    path: Path           # 绝对路径
    relative_path: str   # 相对路径
    hash: str            # MD5，用于增量扫描
    size: int            # 字节数


# 默认忽略的目录
DEFAULT_IGNORE_DIRS = {
    'target', 'build', '.git', '.idea',
    'test', 'tests', 'node_modules', '.gradle',
    'out', 'bin', '.vscode', '.settings'
}


def _calculate_md5(file_path: Path) -> str:
    """计算文件MD5"""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def scan_java_files(
    root_dir: Union[Path, str],
    ignore_dirs: Optional[Set[str]] = None
) -> Iterator[JavaFile]:
    """
    扫描目录下的所有Java文件

    Args:
        root_dir: 项目根目录
        ignore_dirs: 要忽略的目录集合（可选）

    Yields:
        JavaFile: Java文件信息
    """
    root_path = Path(root_dir).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"目录不存在: {root_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"不是目录: {root_path}")

    # 合并默认忽略目录和自定义忽略目录
    ignore = DEFAULT_IGNORE_DIRS.copy()
    if ignore_dirs:
        ignore.update(ignore_dirs)

    for file_path in root_path.rglob('*.java'):
        # 检查是否在忽略目录中
        if any(ignored in file_path.parts for ignored in ignore):
            continue

        try:
            size = file_path.stat().st_size
            file_hash = _calculate_md5(file_path)
            relative = str(file_path.relative_to(root_path))

            yield JavaFile(
                path=file_path,
                relative_path=relative,
                hash=file_hash,
                size=size
            )
        except Exception as e:
            # 跳过无法读取的文件
            print(f"跳过文件 {file_path}: {e}")
            continue


def scan_summary(root_dir: Union[Path, str]) -> dict:
    """
    扫描目录并返回统计信息

    Args:
        root_dir: 项目根目录

    Returns:
        dict: 统计信息
    """
    files = list(scan_java_files(root_dir))

    total_size = sum(f.size for f in files)

    # 按包统计
    packages = {}
    for f in files:
        parts = Path(f.relative_path).parts
        if len(parts) > 1:
            package = '/'.join(parts[:-1])
            packages[package] = packages.get(package, 0) + 1

    return {
        'total_files': len(files),
        'total_size': total_size,
        'total_size_mb': round(total_size / 1024 / 1024, 2),
        'packages': len(packages),
        'top_packages': sorted(
            packages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
    }
