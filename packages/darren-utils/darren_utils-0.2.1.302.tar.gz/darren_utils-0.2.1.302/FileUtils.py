import errno
import fnmatch
import os
import platform
import shutil
import subprocess
import time
from os.path import exists


from send2trash import send2trash




class FileUtils:
    """文件工具类"""
    @staticmethod
    def file_read(path):
        """
        读取文件内容
        
        Args:
            path (str): 文件路径（相对于当前文件所在目录）
            
        Returns:
            str: 文件内容，如果读取失败则返回空字符串
        """
        try:
            script_path = os.path.join(os.path.dirname(__file__), path)
            with open(script_path, 'r', encoding="utf-8") as frd:
                jscode = frd.read()
            return jscode
        except Exception:
            return ""
    @staticmethod
    def file_exists(file_path):
        """
            检查文件是否存在

            Args:
                file_path (str): 文件路径

            Returns:
                bool: 文件存在返回True，否则返回False
            """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        return os.path.exists(file_path) and os.path.isfile(file_path)

    @staticmethod
    def dir_exists(dir_path):
        """
            检查目录是否存在

            Args:
                dir_path (str): 目录路径

            Returns:
                bool: 目录存在返回True，否则返回False
            """
        if not isinstance(dir_path, str):
            raise ValueError("目录路径必须是字符串类型")

        return os.path.exists(dir_path) and os.path.isdir(dir_path)

    @staticmethod
    def file_is_use(file_path):
        """
        检查文件是否被占用

        Args:
            file_path (str): 文件路径

        Returns:
            bool: 文件被占用返回True，否则返回False
        """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        # 首先检查文件是否存在
        if not FileUtils.file_exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 尝试以独占模式打开文件
        try:
            with open(file_path, "r+b") as f:
                pass
            return False  # 文件未被占用
        except IOError as e:
            if e.errno == errno.EACCES:
                return True  # 文件被占用
            else:
                raise  # 其他错误重新抛出

    @staticmethod
    def file_open(file_path, mode='r'):
        """
        打开文件并返回文件句柄，如果失败则返回-1

        Args:
            file_path (str): 文件路径
            mode (str): 文件打开模式，默认为'r'(只读)

        Returns:
            file object or int: 成功时返回文件句柄，失败时返回-1
        """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        if not isinstance(mode, str):
            raise ValueError("文件打开模式必须是字符串类型")

        try:
            file_handle = open(file_path, mode)
            return file_handle
        except Exception:
            return -1

    @staticmethod
    def file_execute(file_path):
        """
        执行文件，如运行exe程序或用默认程序打开文件

        Args:
            file_path (str): 文件路径

        Returns:
            subprocess.Popen or bool or int: 成功时返回进程对象或True，失败时返回-1
        """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        # 检查文件是否存在
        if not FileUtils.file_exists(file_path):
            return -1

        try:
            system = platform.system()
            if system == "Windows":
                # Windows系统使用os.startfile
                os.startfile(file_path)
                return True
            elif system == "Darwin":
                # macOS系统使用open命令
                process = subprocess.Popen(["open", file_path])
                return process
            elif system == "Linux":
                # Linux系统使用xdg-open命令
                process = subprocess.Popen(["xdg-open", file_path])
                return process
            else:
                # 其他系统尝试使用subprocess
                process = subprocess.Popen([file_path])
                return process
        except Exception:
            return -1

    @staticmethod
    def file_locate(file_path):
        """
            在文件管理器中定位文件，打开文件所在目录并选中该文件

            Args:
                file_path (str): 文件路径

            Returns:
                bool or int: 成功时返回True，失败时返回-1
            """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        # 检查文件是否存在
        if not FileUtils.file_exists(file_path):
            return -1

        try:
            system = platform.system()
            if system == "Windows":
                # Windows系统使用explorer命令，并加上/select参数来选中文件
                subprocess.Popen(['explorer', '/select,', os.path.abspath(file_path)])
                return True
            elif system == "Darwin":
                # macOS系统使用open命令定位文件
                subprocess.Popen(['open', '-R', file_path])
                return True
            elif system == "Linux":
                # Linux系统打开文件所在目录（大多数文件管理器不支持直接选中文件）
                directory = os.path.dirname(os.path.abspath(file_path))
                subprocess.Popen(['xdg-open', directory])
                return True
            else:
                # 其他系统打开文件所在目录
                directory = os.path.dirname(os.path.abspath(file_path))
                subprocess.Popen(['open', directory])  # 尝试使用macOS的open命令
                return True
        except Exception:
            return -1

    @staticmethod
    def file_copy(src_path, dest_path, overwrite=False):
        """
            复制文件

            Args:
                src_path (str): 源文件路径
                dest_path (str): 目标文件路径
                overwrite (bool): 是否覆盖已存在的文件，默认为False

            Returns:
                bool or int: 成功时返回True，失败时返回-1
            """
        if not isinstance(src_path, str):
            raise ValueError("源文件路径必须是字符串类型")

        if not isinstance(dest_path, str):
            raise ValueError("目标文件路径必须是字符串类型")

        if not isinstance(overwrite, bool):
            raise ValueError("overwrite参数必须是布尔类型")

        # 检查源文件是否存在
        if not FileUtils.file_exists(src_path):
            return -1

        # 检查目标文件是否存在且不允许覆盖
        if FileUtils.file_exists(dest_path) and not overwrite:
            return -1

        try:
            # 执行文件复制
            shutil.copy2(src_path, dest_path)
            return True
        except Exception:
            return -1

    @staticmethod
    def file_rename(old_name, new_name):
        """
            重命名文件

            Args:
                old_name (str): 原文件名
                new_name (str): 新文件名

            Returns:
                bool or int: 成功时返回True，失败时返回-1
            """
        if not isinstance(old_name, str):
            raise ValueError("原文件名必须是字符串类型")

        if not isinstance(new_name, str):
            raise ValueError("新文件名必须是字符串类型")

        # 检查原文件是否存在
        if not FileUtils.file_exists(old_name):
            return -1

        # 检查新文件名是否已存在
        if FileUtils.file_exists(new_name):
            return -1

        try:
            # 执行文件重命名
            os.rename(old_name, new_name)
            return True
        except Exception:
            return -1

    @staticmethod
    def file_enumerate(directory, pattern="*.*", with_path=False, sort_alpha=False, recursive=False):
        """
            枚举某个目录下的指定类型文件

            Args:
                directory (str): 欲寻找的目录
                pattern (str): 欲寻找的文件名(如果寻找全部文件可以填入*.*，或*.txt只找txt文件, 多个后缀中间用"|"隔开)
                with_path (bool): 是否带路径(默认为假； 真=带目录路径，如C:\012.txt； 假=不带，如 012.txt)
                sort_alpha (bool): 是否按字母排序(默认为假；真=按字母a-z排序 假=不排序)
                recursive (bool): 是否遍历子目录(默认为假)

            Returns:
                list or int: 成功时返回文件列表，失败时返回-1
            """
        if not isinstance(directory, str):
            raise ValueError("目录必须是字符串类型")

        if not isinstance(pattern, str):
            raise ValueError("文件名模式必须是字符串类型")

        if not isinstance(with_path, bool):
            raise ValueError("with_path参数必须是布尔类型")

        if not isinstance(sort_alpha, bool):
            raise ValueError("sort_alpha参数必须是布尔类型")

        if not isinstance(recursive, bool):
            raise ValueError("recursive参数必须是布尔类型")

        # 检查目录是否存在
        if not FileUtils.dir_exists(directory):
            return -1

        try:
            files = []

            # 处理多个文件模式（用 | 分隔）
            patterns = pattern.split("|")
            patterns = [p.strip() for p in patterns]

            # 根据是否递归选择不同的遍历方法
            if recursive:
                # 递归遍历所有子目录
                for root, _, filenames in os.walk(directory):
                    for filename in filenames:
                        # 检查文件是否匹配任一模式
                        for pat in patterns:
                            if fnmatch.fnmatch(filename, pat):
                                if with_path:
                                    files.append(os.path.join(root, filename))
                                else:
                                    files.append(filename)
                                break  # 匹配到一个就够了，避免重复添加
            else:
                # 只遍历当前目录
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    # 检查是否为文件（而不是目录）
                    if os.path.isfile(file_path):
                        # 检查文件是否匹配任一模式
                        for pat in patterns:
                            if fnmatch.fnmatch(filename, pat):
                                if with_path:
                                    files.append(file_path)
                                else:
                                    files.append(filename)
                                break  # 匹配到一个就够了，避免重复添加

            # 如果需要按字母排序
            if sort_alpha:
                files.sort()

            return files
        except Exception:
            return -1

    @staticmethod
    def file_size(file_path, unit="M"):
        """
            获取文件大小

            Args:
                file_path (str): 文件路径
                unit (str): 返回大小的单位(B、KB、MB、GB)，默认为M

            Returns:
                str or int: 成功时返回格式化的文件大小字符串，失败时返回-1
            """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        if not isinstance(unit, str):
            raise ValueError("单位必须是字符串类型")

        # 检查文件是否存在
        if not FileUtils.file_exists(file_path):
            return -1

        try:
            # 获取文件大小（字节）
            size_bytes = os.path.getsize(file_path)

            # 定义单位映射
            units = {
                'B': 0,
                'KB': 1,
                'MB': 2,
                'GB': 3
            }

            # 转换为大写并检查单位是否有效
            unit = unit.upper()
            if unit not in units:
                unit = "MB"  # 默认使用MB

            # 计算对应的单位大小
            if size_bytes == 0:
                return f"0 {unit}"

            # 计算大小
            size = size_bytes / (1024 ** units[unit])

            # 格式化输出
            if size >= 1000:
                return f"{size:.2f} {unit}"
            elif size >= 100:
                return f"{size:.3f} {unit}"
            elif size >= 10:
                return f"{size:.4f} {unit}"
            else:
                return f"{size:.5f} {unit}"

        except Exception:
            return -1

    @staticmethod
    def file_get_extension(file_path):
        """
            获取文件扩展名

            Args:
                file_path (str): 文件路径

            Returns:
                str or int: 成功时返回文件扩展名（如：.jpg），没有扩展名时返回空字符串，失败时返回-1
            """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        try:
            # 使用os.path.splitext获取文件扩展名
            _, extension = os.path.splitext(file_path)
            return extension
        except Exception:
            return -1

    @staticmethod
    def file_get_directory(file_path):
        """
            获取文件所在目录路径

            Args:
                file_path (str): 文件路径

            Returns:
                str or int: 成功时返回文件所在目录路径，失败时返回-1
            """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        try:
            # 使用os.path.dirname获取文件所在目录
            directory = os.path.dirname(file_path)

            # 如果目录为空，说明是相对路径的文件，返回当前目录
            if directory == "":
                return "."

            # 确保目录路径末尾有路径分隔符
            if not directory.endswith(os.sep):
                directory += os.sep

            return directory
        except Exception:
            return -1

    @staticmethod
    def file_get_info(file_path):
        """
            获取文件信息

            Args:
                file_path (str): 文件路径

            Returns:
                dict or int: 成功时返回包含文件信息的字典，失败时返回-1
            """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        # 检查文件是否存在
        if not FileUtils.file_exists(file_path):
            return -1

        try:
            # 获取文件统计信息
            stat_info = os.stat(file_path)

            # 获取文件基本信息
            file_info = {
                "name": os.path.basename(file_path),  # 文件名
                "path": file_path,  # 完整路径
                "directory": FileUtils.file_get_directory(file_path),  # 所在目录
                "extension": FileUtils.file_get_extension(file_path),  # 扩展名
                "size_bytes": stat_info.st_size,  # 文件大小（字节）
                "size_formatted": FileUtils.file_size(file_path, "MB"),  # 格式化文件大小
                "created_time": time.ctime(stat_info.st_ctime),  # 创建时间
                "modified_time": time.ctime(stat_info.st_mtime),  # 修改时间
                "accessed_time": time.ctime(stat_info.st_atime),  # 访问时间
                "is_readable": os.access(file_path, os.R_OK),  # 是否可读
                "is_writable": os.access(file_path, os.W_OK),  # 是否可写
                "is_executable": os.access(file_path, os.X_OK)  # 是否可执行
            }

            return file_info
        except Exception:
            return -1

    @staticmethod
    def file_get_name(file_path, with_extension=False):
        """
            获取文件名

            Args:
                file_path (str): 文件路径
                with_extension (bool): 是否带后缀，默认为False，不带后缀；True为带后缀

            Returns:
                str or int: 成功时返回文件名，失败时返回-1
            """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        if not isinstance(with_extension, bool):
            raise ValueError("with_extension参数必须是布尔类型")

        try:
            # 获取文件名（带后缀）
            file_name_with_ext = os.path.basename(file_path)

            # 如果需要带后缀，直接返回
            if with_extension:
                return file_name_with_ext

            # 如果不需要带后缀，去掉后缀后再返回
            file_name_without_ext = os.path.splitext(file_name_with_ext)[0]
            return file_name_without_ext
        except Exception:
            return -1

    @staticmethod
    def file_delete(file_path, to_trash=True):
        """
            删除文件

            Args:
                file_path (str): 文件路径
                to_trash (bool): 是否删除到回收站，默认为True（删除到回收站）；False为彻底删除

            Returns:
                bool or int: 成功时返回True，失败时返回-1
            """
        if not isinstance(file_path, str):
            raise ValueError("文件路径必须是字符串类型")

        if not isinstance(to_trash, bool):
            raise ValueError("to_trash参数必须是布尔类型")

        # 检查文件是否存在
        if not exists(file_path):
            return -1

        try:
            if to_trash:
                send2trash(file_path)
            else:
                # 彻底删除
                os.remove(file_path)

            return True
        except Exception:
            return -1