import os
import shutil
import json
import yaml
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import zipfile
import tarfile
from utils.logging.logger import logger


class FileHelper:
    """文件操作辅助工具"""
    
    @staticmethod
    def read_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            文件内容
        """
        try:
            file_path = Path(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            logger.debug(f"读取文件成功: {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def write_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8', 
                  create_dirs: bool = True):
        """
        写入文件内容
        
        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 文件编码
            create_dirs: 是否创建目录
        """
        try:
            file_path = Path(file_path)
            
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            logger.debug(f"写入文件成功: {file_path}")
            
        except Exception as e:
            logger.error(f"写入文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def append_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8'):
        """
        追加文件内容
        
        Args:
            file_path: 文件路径
            content: 追加内容
            encoding: 文件编码
        """
        try:
            file_path = Path(file_path)
            
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
            
            logger.debug(f"追加文件成功: {file_path}")
            
        except Exception as e:
            logger.error(f"追加文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        读取JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            JSON数据
        """
        try:
            file_path = Path(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"读取JSON文件成功: {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"读取JSON文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def write_json(file_path: Union[str, Path], data: Dict[str, Any], 
                  indent: int = 2, create_dirs: bool = True):
        """
        写入JSON文件
        
        Args:
            file_path: 文件路径
            data: JSON数据
            indent: 缩进空格数
            create_dirs: 是否创建目录
        """
        try:
            file_path = Path(file_path)
            
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            
            logger.debug(f"写入JSON文件成功: {file_path}")
            
        except Exception as e:
            logger.error(f"写入JSON文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def read_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        读取YAML文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            YAML数据
        """
        try:
            file_path = Path(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            logger.debug(f"读取YAML文件成功: {file_path}")
            return data or {}
            
        except Exception as e:
            logger.error(f"读取YAML文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def write_yaml(file_path: Union[str, Path], data: Dict[str, Any], 
                  create_dirs: bool = True):
        """
        写入YAML文件
        
        Args:
            file_path: 文件路径
            data: YAML数据
            create_dirs: 是否创建目录
        """
        try:
            file_path = Path(file_path)
            
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            logger.debug(f"写入YAML文件成功: {file_path}")
            
        except Exception as e:
            logger.error(f"写入YAML文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def read_csv(file_path: Union[str, Path], encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        读取CSV文件
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            CSV数据列表
        """
        try:
            file_path = Path(file_path)
            data = []
            
            with open(file_path, 'r', encoding=encoding, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(dict(row))
            
            logger.debug(f"读取CSV文件成功: {file_path}, 行数: {len(data)}")
            return data
            
        except Exception as e:
            logger.error(f"读取CSV文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def write_csv(file_path: Union[str, Path], data: List[Dict[str, Any]], 
                 fieldnames: List[str] = None, encoding: str = 'utf-8', 
                 create_dirs: bool = True):
        """
        写入CSV文件
        
        Args:
            file_path: 文件路径
            data: CSV数据
            fieldnames: 字段名列表
            encoding: 文件编码
            create_dirs: 是否创建目录
        """
        try:
            file_path = Path(file_path)
            
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not data:
                return
            
            if fieldnames is None:
                fieldnames = list(data[0].keys())
            
            with open(file_path, 'w', encoding=encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.debug(f"写入CSV文件成功: {file_path}, 行数: {len(data)}")
            
        except Exception as e:
            logger.error(f"写入CSV文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path], create_dirs: bool = True):
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            create_dirs: 是否创建目录
        """
        try:
            src = Path(src)
            dst = Path(dst)
            
            if create_dirs:
                dst.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src, dst)
            logger.debug(f"复制文件成功: {src} -> {dst}")
            
        except Exception as e:
            logger.error(f"复制文件失败: {src} -> {dst}, 错误: {e}")
            raise
    
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path], create_dirs: bool = True):
        """
        移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            create_dirs: 是否创建目录
        """
        try:
            src = Path(src)
            dst = Path(dst)
            
            if create_dirs:
                dst.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src), str(dst))
            logger.debug(f"移动文件成功: {src} -> {dst}")
            
        except Exception as e:
            logger.error(f"移动文件失败: {src} -> {dst}, 错误: {e}")
            raise
    
    @staticmethod
    def remove_file(file_path: Union[str, Path]):
        """
        删除文件
        
        Args:
            file_path: 文件路径
        """
        try:
            file_path = Path(file_path)
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"删除文件成功: {file_path}")
            
        except Exception as e:
            logger.error(f"删除文件失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def create_directory(dir_path: Union[str, Path], parents: bool = True, exist_ok: bool = True):
        """
        创建目录
        
        Args:
            dir_path: 目录路径
            parents: 是否创建父目录
            exist_ok: 目录存在时是否报错
        """
        try:
            dir_path = Path(dir_path)
            dir_path.mkdir(parents=parents, exist_ok=exist_ok)
            logger.debug(f"创建目录成功: {dir_path}")
            
        except Exception as e:
            logger.error(f"创建目录失败: {dir_path}, 错误: {e}")
            raise
    
    @staticmethod
    def remove_directory(dir_path: Union[str, Path]):
        """
        删除目录
        
        Args:
            dir_path: 目录路径
        """
        try:
            dir_path = Path(dir_path)
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.debug(f"删除目录成功: {dir_path}")
            
        except Exception as e:
            logger.error(f"删除目录失败: {dir_path}, 错误: {e}")
            raise
    
    @staticmethod
    def list_files(dir_path: Union[str, Path], pattern: str = "*", 
                  recursive: bool = False) -> List[Path]:
        """
        列出目录中的文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件模式
            recursive: 是否递归
            
        Returns:
            文件路径列表
        """
        try:
            dir_path = Path(dir_path)
            
            if recursive:
                files = list(dir_path.rglob(pattern))
            else:
                files = list(dir_path.glob(pattern))
            
            # 只返回文件，不包括目录
            files = [f for f in files if f.is_file()]
            
            logger.debug(f"列出文件成功: {dir_path}, 找到{len(files)}个文件")
            return files
            
        except Exception as e:
            logger.error(f"列出文件失败: {dir_path}, 错误: {e}")
            raise
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        try:
            file_path = Path(file_path)
            size = file_path.stat().st_size
            logger.debug(f"获取文件大小: {file_path} = {size} bytes")
            return size
            
        except Exception as e:
            logger.error(f"获取文件大小失败: {file_path}, 错误: {e}")
            raise
    
    @staticmethod
    def file_exists(file_path: Union[str, Path]) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否存在
        """
        return Path(file_path).exists()
    
    @staticmethod
    def is_file(path: Union[str, Path]) -> bool:
        """
        检查路径是否为文件
        
        Args:
            path: 路径
            
        Returns:
            是否为文件
        """
        return Path(path).is_file()
    
    @staticmethod
    def is_directory(path: Union[str, Path]) -> bool:
        """
        检查路径是否为目录
        
        Args:
            path: 路径
            
        Returns:
            是否为目录
        """
        return Path(path).is_dir()
    
    @staticmethod
    def get_file_extension(file_path: Union[str, Path]) -> str:
        """
        获取文件扩展名
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件扩展名
        """
        return Path(file_path).suffix.lower()
    
    @staticmethod
    def get_file_name(file_path: Union[str, Path], with_extension: bool = True) -> str:
        """
        获取文件名

        Args:
            file_path: 文件路径
            with_extension: 是否包含扩展名

        Returns:
            文件名
        """
        path = Path(file_path)
        if with_extension:
            return path.name
        else:
            return path.stem

    @staticmethod
    def create_zip_archive(zip_path: Union[str, Path], files: List[Union[str, Path]],
                          base_dir: Union[str, Path] = None):
        """
        创建ZIP压缩包

        Args:
            zip_path: 压缩包路径
            files: 要压缩的文件列表
            base_dir: 基础目录，用于计算相对路径
        """
        try:
            zip_path = Path(zip_path)
            zip_path.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files:
                    file_path = Path(file_path)

                    if file_path.is_file():
                        if base_dir:
                            arcname = file_path.relative_to(base_dir)
                        else:
                            arcname = file_path.name

                        zipf.write(file_path, arcname)
                    elif file_path.is_dir():
                        for sub_file in file_path.rglob('*'):
                            if sub_file.is_file():
                                if base_dir:
                                    arcname = sub_file.relative_to(base_dir)
                                else:
                                    arcname = sub_file.relative_to(file_path.parent)

                                zipf.write(sub_file, arcname)

            logger.info(f"创建ZIP压缩包成功: {zip_path}")

        except Exception as e:
            logger.error(f"创建ZIP压缩包失败: {zip_path}, 错误: {e}")
            raise

    @staticmethod
    def extract_zip_archive(zip_path: Union[str, Path], extract_dir: Union[str, Path]):
        """
        解压ZIP压缩包

        Args:
            zip_path: 压缩包路径
            extract_dir: 解压目录
        """
        try:
            zip_path = Path(zip_path)
            extract_dir = Path(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_dir)

            logger.info(f"解压ZIP压缩包成功: {zip_path} -> {extract_dir}")

        except Exception as e:
            logger.error(f"解压ZIP压缩包失败: {zip_path}, 错误: {e}")
            raise

    @staticmethod
    def create_tar_archive(tar_path: Union[str, Path], files: List[Union[str, Path]],
                          compression: str = 'gz', base_dir: Union[str, Path] = None):
        """
        创建TAR压缩包

        Args:
            tar_path: 压缩包路径
            files: 要压缩的文件列表
            compression: 压缩格式 (gz, bz2, xz)
            base_dir: 基础目录，用于计算相对路径
        """
        try:
            tar_path = Path(tar_path)
            tar_path.parent.mkdir(parents=True, exist_ok=True)

            mode_map = {
                'gz': 'w:gz',
                'bz2': 'w:bz2',
                'xz': 'w:xz',
                '': 'w'
            }

            mode = mode_map.get(compression, 'w:gz')

            with tarfile.open(tar_path, mode) as tarf:
                for file_path in files:
                    file_path = Path(file_path)

                    if base_dir:
                        arcname = file_path.relative_to(base_dir)
                    else:
                        arcname = file_path.name

                    tarf.add(file_path, arcname=arcname)

            logger.info(f"创建TAR压缩包成功: {tar_path}")

        except Exception as e:
            logger.error(f"创建TAR压缩包失败: {tar_path}, 错误: {e}")
            raise

    @staticmethod
    def extract_tar_archive(tar_path: Union[str, Path], extract_dir: Union[str, Path]):
        """
        解压TAR压缩包

        Args:
            tar_path: 压缩包路径
            extract_dir: 解压目录
        """
        try:
            tar_path = Path(tar_path)
            extract_dir = Path(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)

            with tarfile.open(tar_path, 'r:*') as tarf:
                tarf.extractall(extract_dir)

            logger.info(f"解压TAR压缩包成功: {tar_path} -> {extract_dir}")

        except Exception as e:
            logger.error(f"解压TAR压缩包失败: {tar_path}, 错误: {e}")
            raise

    @staticmethod
    def clean_directory(dir_path: Union[str, Path], keep_patterns: List[str] = None):
        """
        清理目录内容

        Args:
            dir_path: 目录路径
            keep_patterns: 保留的文件模式列表
        """
        try:
            dir_path = Path(dir_path)

            if not dir_path.exists():
                return

            keep_patterns = keep_patterns or []

            for item in dir_path.iterdir():
                should_keep = False

                # 检查是否匹配保留模式
                for pattern in keep_patterns:
                    if item.match(pattern):
                        should_keep = True
                        break

                if not should_keep:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)

            logger.info(f"清理目录成功: {dir_path}")

        except Exception as e:
            logger.error(f"清理目录失败: {dir_path}, 错误: {e}")
            raise

    @staticmethod
    def backup_file(file_path: Union[str, Path], backup_dir: Union[str, Path] = None,
                   timestamp: bool = True) -> Path:
        """
        备份文件

        Args:
            file_path: 源文件路径
            backup_dir: 备份目录
            timestamp: 是否添加时间戳

        Returns:
            备份文件路径
        """
        try:
            file_path = Path(file_path)

            if backup_dir is None:
                backup_dir = file_path.parent / "backup"
            else:
                backup_dir = Path(backup_dir)

            backup_dir.mkdir(parents=True, exist_ok=True)

            if timestamp:
                import datetime
                timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{file_path.stem}_{timestamp_str}{file_path.suffix}"
            else:
                backup_name = file_path.name

            backup_path = backup_dir / backup_name

            shutil.copy2(file_path, backup_path)
            logger.info(f"备份文件成功: {file_path} -> {backup_path}")

            return backup_path

        except Exception as e:
            logger.error(f"备份文件失败: {file_path}, 错误: {e}")
            raise


# 全局文件助手实例
file_helper = FileHelper()

# 便捷函数
def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """读取JSON文件的便捷函数"""
    return FileHelper.read_json(file_path)

def write_json(file_path: Union[str, Path], data: Dict[str, Any]):
    """写入JSON文件的便捷函数"""
    FileHelper.write_json(file_path, data)

def read_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """读取YAML文件的便捷函数"""
    return FileHelper.read_yaml(file_path)

def write_yaml(file_path: Union[str, Path], data: Dict[str, Any]):
    """写入YAML文件的便捷函数"""
    FileHelper.write_yaml(file_path, data)
