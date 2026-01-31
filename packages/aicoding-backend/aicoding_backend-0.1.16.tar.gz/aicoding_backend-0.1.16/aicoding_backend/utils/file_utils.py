"""
文件操作工具模块
提供常用的文件和目录操作功能
"""
import os
from pathlib import Path
from typing import Union


def file_exists(file_path: Union[str, Path]) -> bool:
    """
    检查文件是否存在
    
    Args:
        file_path: 文件路径，可以是字符串或Path对象
        
    Returns:
        bool: 如果文件存在返回True，否则返回False
        
    Examples:
        >>> file_exists("test.txt")
        True
        >>> file_exists("/path/to/nonexistent.txt")
        False
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except (OSError, ValueError):
        return False


def dir_exists(dir_path: Union[str, Path]) -> bool:
    """
    检查目录是否存在
    
    Args:
        dir_path: 目录路径，可以是字符串或Path对象
        
    Returns:
        bool: 如果目录存在返回True，否则返回False
    """
    try:
        path = Path(dir_path)
        return path.exists() and path.is_dir()
    except (OSError, ValueError):
        return False


def ensure_dir(dir_path: Union[str, Path]) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        dir_path: 目录路径
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    try:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, ValueError):
        return False


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        int: 文件大小，如果文件不存在返回-1
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            return path.stat().st_size
        return -1
    except (OSError, ValueError):
        return -1
    

def write_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径，可以是字符串或Path对象
        content: 要写入的内容
        encoding: 文件编码，默认utf-8
        
    Returns:
        bool: 成功返回True，失败返回False
        
    Examples:
        >>> write_file("test.txt", "Hello World")
        True
    """
    try:
        path = Path(file_path)
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        # 写入文件
        path.write_text(content, encoding=encoding)
        return True
    except (OSError, ValueError, UnicodeEncodeError) as e:
        print(f"写入文件失败 {file_path}: {e}")
        return False


def read_dir(dir_path: Union[str, Path]) -> list:
    """
    读取目录内容，返回文件和子目录列表
    
    Args:
        dir_path: 目录路径
        
    Returns:
        list: 目录中的文件和子目录名称列表
    """
    try:
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            return []
        return [item.name for item in path.iterdir()]
    except (OSError, ValueError):
        return []


if __name__=="__main__":
    print(dir_exists("/Users/chenshuren.5/proj/trade-operations-agent"))