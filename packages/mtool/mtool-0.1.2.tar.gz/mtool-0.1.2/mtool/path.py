import os
import sys
from pathlib import Path
from typing import Optional


def get_app_dir() -> str:
    """获取程序根目录

    Returns:
        str: 程序根目录路径

    Note:
        - 源码运行：返回 main.py 所在目录
        - PyInstaller / Nuitka 打包：返回 exe 所在目录
    """
    if "__compiled__" in globals():
        # Nuitka：argv[0] 保存的是原始 exe 路径
        return os.path.dirname(os.path.abspath(sys.argv[0]))

    # PyInstaller / 普通 exe
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))

    # 源码运行
    return os.path.dirname(os.path.abspath(sys.modules["__main__"].__file__))


def get_resource_path(*paths) -> Path:
    """获取资源路径，兼容多种运行环境包括Nuitka onefile模式。

    Args:
        *paths: 资源路径的各个部分

    Returns:
        Path: 完整的资源路径对象
    """
    # 首先尝试在多个可能的位置查找资源
    candidate_bases = []
    
    # 检查是否打包运行（PyInstaller或Nuitka）
    if getattr(sys, "frozen", False):
        # PyInstaller打包：使用_MEIPASS
        if hasattr(sys, "_MEIPASS"):
            candidate_bases.append(Path(sys._MEIPASS))
        # Nuitka或其他打包：使用可执行文件所在目录
        else:
            candidate_bases.append(Path(os.path.dirname(os.path.abspath(sys.executable))))
    else:
        # 源码运行：使用脚本所在目录
        candidate_bases.append(Path(os.path.dirname(os.path.abspath(__file__))).parent)
        
    # 添加当前工作目录作为备选
    candidate_bases.append(Path.cwd())
    
    # 尝试每个候选基础路径
    for base in candidate_bases:
        resource_path = base.joinpath(*paths)
        if resource_path.exists():
            return resource_path
    
    # 如果在任何基础路径下都找不到，尝试直接作为相对路径
    relative_path = Path(*paths)
    if relative_path.exists():
        return relative_path
    
    # 如果都不存在，返回最可能的基础路径下的组合
    return candidate_bases[0].joinpath(*paths)


def get_data_directory(sub_dir: str = "") -> str:
    """获取数据目录路径（如input、output目录），兼容所有运行环境。

    Args:
        sub_dir: 子目录名称，如'input'、'output'

    Returns:
        完整的数据目录路径
    """
    # 使用通用的程序目录获取函数
    root_dir = get_app_dir()

    # 构建完整的目录路径
    if sub_dir:
        # 规范化子目录路径，去除尾部斜杠以确保正确拼接
        normalized_sub_dir = sub_dir.rstrip("/").rstrip("\\")
        return os.path.join(root_dir, normalized_sub_dir)
    return root_dir
