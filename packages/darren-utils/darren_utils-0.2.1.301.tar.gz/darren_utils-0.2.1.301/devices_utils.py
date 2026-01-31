import sys
import subprocess
import platform
import os
import re
from typing import Dict,  Optional


def execute_cmd(cmd: str, encoding: str = "utf-8", need_sudo: bool = False) -> str:
    """
    通用命令执行函数：适配Windows/Linux编码，自动处理sudo权限
    :param cmd: 执行的命令
    :param encoding: 编码（Windows=cp936/gbk，Linux=utf-8）
    :param need_sudo: 是否需要sudo（仅Linux）
    :return: 清洗后的命令输出
    """
    if need_sudo and sys.platform == "linux" and os.geteuid() != 0:
        cmd = f"sudo {cmd}"

    try:
        output = subprocess.check_output(
            cmd, shell=True, encoding=encoding, errors="ignore",
            stderr=subprocess.DEVNULL
        ).strip()
        # 清洗空行和多余空格
        return "\n".join([line.strip() for line in output.split("\n") if line.strip()])
    except Exception:
        return ""


def get_linux_disk_device() -> str:
    """自动识别Linux系统盘设备名（兼容sda/vda/xvda等）"""
    # 方式1：从/etc/mtab获取根分区设备
    mtab_cmd = 'cat /etc/mtab | grep " / " | awk \'{print $1}\''
    root_dev = execute_cmd(mtab_cmd)
    if root_dev:
        # 提取设备名（如/dev/sda1 → sda，/dev/vda2 → vda）
        dev_name = re.sub(r'\/dev\/(\w+)\d+', r'\1', root_dev)
        return dev_name if dev_name else "sda"
    # 方式2：兜底返回sda
    return "sda"


def get_hardware_identifier() -> Dict[str, Optional[str]]:
    """
    跨Windows/Linux精准获取硬件标识（优化Linux兼容性，适配CentOS 9/虚拟化环境）
    """
    result = {
        "os": platform.system(),
        "motherboard_serial": None,  # 主板序列号
        "bios_serial": None,  # BIOS序列号
        "cpu_serial": None,  # CPU序列号
        "disk_serial": None,  # 硬盘序列号（硬件/卷序列号兜底）
        "gpu_info": None,  # 显卡信息（所有显卡|分隔）
        "cpu_info": None,  # CPU型号
        "system_version": None,  # 系统版本
        "system_uuid": None,  # 系统UUID
        "physical_gpu": None,  # 物理显卡
        #"device_unique_id": None  # 设备唯一标识（兜底方案）
    }

    # ========== 1. Windows系统（保留精准逻辑） ==========
    if sys.platform == "win32":
        # 1.1 主板序列号
        mb_cmd = 'wmic baseboard get serialnumber'
        mb_output = execute_cmd(mb_cmd, encoding="cp936")
        result["motherboard_serial"] = mb_output.split("\n")[1].strip() if len(mb_output.split("\n")) >= 2 else "未知"

        # 1.2 BIOS序列号
        bios_cmd = 'wmic bios get serialnumber'
        bios_output = execute_cmd(bios_cmd, encoding="cp936")
        result["bios_serial"] = bios_output.split("\n")[1].strip() if len(
            bios_output.split("\n")) >= 2 else "SYSTEM SERIAL NUMBER"

        # 1.3 CPU序列号
        cpu_serial_cmd = 'wmic cpu get processorid'
        cpu_serial_output = execute_cmd(cpu_serial_cmd, encoding="cp936")
        result["cpu_serial"] = cpu_serial_output.split("\n")[1].strip() if len(
            cpu_serial_output.split("\n")) >= 2 else "未知"

        # 1.4 CPU型号
        cpu_model_cmd = 'wmic cpu get name'
        cpu_model_output = execute_cmd(cpu_model_cmd, encoding="cp936")
        result["cpu_info"] = cpu_model_output.split("\n")[1].strip() if len(
            cpu_model_output.split("\n")) >= 2 else platform.processor()

        # 1.5 硬盘序列号
        disk_cmd = 'wmic diskdrive get serialnumber'
        disk_output = execute_cmd(disk_cmd, encoding="cp936")
        disk_lines = disk_output.split("\n")[1:]
        valid_disks = [line.strip() for line in disk_lines if line.strip() and line.strip() != "None"]
        result["disk_serial"] = " ".join(valid_disks) if valid_disks else "未知"

        # 1.6 显卡信息
        gpu_cmd = 'wmic path win32_VideoController get name'
        gpu_output = execute_cmd(gpu_cmd, encoding="cp936")
        gpu_lines = gpu_output.split("\n")[1:]
        valid_gpus = [line.strip().upper() for line in gpu_lines if line.strip() and line.strip() != "None"]
        result["gpu_info"] = "| ".join(valid_gpus) + "|" if valid_gpus else "未知"
        # 过滤物理显卡
        virtual_keywords = ["VIRTUAL", "REMOTE", "MICROSOFT BASIC", "GAMEVIEWER"]
        physical_gpus = [gpu for gpu in valid_gpus if not any(kw in gpu for kw in virtual_keywords)]
        result["physical_gpu"] = physical_gpus[0] if physical_gpus else "未知"

        # 1.7 系统版本
        try:
            os_ver = platform.version()
            os_release = platform.release()
            os_name = platform.system().upper()
            result["system_version"] = f"{os_name}_{os_release}_{os_ver}"
        except:
            result["system_version"] = "未知"

        # 1.8 系统UUID
        uuid_cmd = 'wmic csproduct get uuid'
        uuid_output = execute_cmd(uuid_cmd, encoding="cp936")
        result["system_uuid"] = uuid_output.split("\n")[1].strip().upper() if len(
            uuid_output.split("\n")) >= 2 else "未知"

    # ========== 2. Linux系统（深度兼容CentOS 9/虚拟化环境） ==========
    elif sys.platform == "linux":
        # 2.1 主板序列号（多层备用方案）
        mb_serial = "未知"
        # 方案1：dmidecode baseboard-serial
        mb_cmd1 = 'dmidecode -s baseboard-serial-number'
        mb_output1 = execute_cmd(mb_cmd1, need_sudo=True)
        if mb_output1 and mb_output1 not in ["Not Applicable", ""]:
            mb_serial = mb_output1
        # 方案2：dmidecode system-serial（备用）
        else:
            mb_cmd2 = 'dmidecode -s system-serial-number'
            mb_output2 = execute_cmd(mb_cmd2, need_sudo=True)
            if mb_output2 and mb_output2 not in ["Not Applicable", ""]:
                mb_serial = mb_output2
        result["motherboard_serial"] = mb_serial

        # 2.2 BIOS序列号
        bios_cmd = 'dmidecode -s bios-version'
        bios_output = execute_cmd(bios_cmd, need_sudo=True)
        result["bios_serial"] = bios_output if bios_output else "SYSTEM SERIAL NUMBER"

        # 2.3 CPU序列号（多层备用）
        cpu_serial = "未知"
        # 方案1：dmidecode processor-id
        cpu_cmd1 = 'dmidecode -s processor-id'
        cpu_output1 = execute_cmd(cpu_cmd1, need_sudo=True)
        if cpu_output1 and cpu_output1 not in ["Not Applicable", ""]:
            cpu_serial = cpu_output1
        # 方案2：cpuid（备用）
        else:
            cpu_cmd2 = 'cpuid | grep "Processor serial number" | cut -d: -f2'
            cpu_output2 = execute_cmd(cpu_cmd2).strip()
            if cpu_output2:
                cpu_serial = cpu_output2
        result["cpu_serial"] = cpu_serial

        # 2.4 CPU型号（精准解析）
        cpu_model = "未知"
        cpu_cmd = 'cat /proc/cpuinfo | grep -m1 "model name" | cut -d: -f2 | sed "s/^ *//g"'
        cpu_output = execute_cmd(cpu_cmd)
        if cpu_output:
            cpu_model = cpu_output
        result["cpu_info"] = cpu_model

        # 2.5 硬盘序列号（自动识别设备+卷序列号兜底）
        disk_serial = "未知"
        # 步骤1：自动识别系统盘设备名（sda/vda/xvda等）
        dev_name = get_linux_disk_device()  # 如sda/vda
        # 方案1：lsblk serial
        disk_cmd1 = f'lsblk -no serial /dev/{dev_name}'
        disk_output1 = execute_cmd(disk_cmd1)
        if disk_output1 and disk_output1 not in ["", "unknown"]:
            disk_serial = disk_output1
        # 方案2：hdparm（备用）
        else:
            disk_cmd2 = f'hdparm -I /dev/{dev_name} 2>/dev/null | grep "Serial Number" | cut -d: -f2'
            disk_output2 = execute_cmd(disk_cmd2).strip()
            if disk_output2:
                disk_serial = disk_output2
        # 方案3：blkid卷序列号（终极兜底）
        if disk_serial == "未知":
            disk_cmd3 = f'blkid /dev/{dev_name}1 2>/dev/null | grep "UUID" | cut -d= -f2 | sed "s/\"//g"'
            disk_output3 = execute_cmd(disk_cmd3).strip()
            if disk_output3:
                disk_serial = f"卷序列号-{disk_output3}"
        result["disk_serial"] = disk_serial

        # 2.6 显卡信息
        gpu_list = []
        # 方案1：lshw
        gpu_cmd1 = 'lshw -C display 2>/dev/null | grep -E "product:" | cut -d: -f2 | sed "s/^ *//g"'
        gpu_output1 = execute_cmd(gpu_cmd1, need_sudo=True)
        if gpu_output1:
            gpu_list = [line.strip().upper() for line in gpu_output1.split("\n") if line.strip()]
        # 方案2：nvidia-smi（NVIDIA备用）
        if not gpu_list:
            gpu_cmd2 = 'nvidia-smi --query-gpu=name --format=csv,noheader'
            gpu_output2 = execute_cmd(gpu_cmd2)
            if gpu_output2:
                gpu_list = [line.strip().upper() for line in gpu_output2.split("\n") if line.strip()]
        # 方案3：lspci（终极备用）
        if not gpu_list:
            gpu_cmd3 = 'lspci | grep -i "vga\|3d\|display" | cut -d: -f3 | sed "s/^ *//g"'
            gpu_output3 = execute_cmd(gpu_cmd3)
            if gpu_output3:
                gpu_list = [line.strip().upper() for line in gpu_output3.split("\n") if line.strip()]
        result["gpu_info"] = "| ".join(gpu_list) + "|" if gpu_list else "未知"
        result["physical_gpu"] = gpu_list[0] if gpu_list else "未知"

        # 2.7 系统版本（适配CentOS 9）
        sys_version = "未知"
        try:
            # 方案1：lsb_release（优先）
            distro_name = execute_cmd('lsb_release -si').upper()
            distro_ver = execute_cmd('lsb_release -sr')
            kernel_ver = platform.release()
            if distro_name and distro_ver:
                sys_version = f"LINUX_{distro_name}_{distro_ver}_KERNEL-{kernel_ver}"
            # 方案2：/etc/os-release（备用）
            else:
                os_name = execute_cmd('grep -E "^NAME=" /etc/os-release | cut -d= -f2 | sed "s/\"//g"').upper()
                os_ver = execute_cmd('grep -E "^VERSION_ID=" /etc/os-release | cut -d= -f2 | sed "s/\"//g"')
                if os_name and os_ver:
                    sys_version = f"LINUX_{os_name}_{os_ver}_KERNEL-{kernel_ver}"
                # 方案3：仅内核版本（兜底）
                else:
                    sys_version = f"LINUX_KERNEL-{kernel_ver}"
        except:
            sys_version = f"LINUX_{platform.release()}"
        result["system_version"] = sys_version

        # 2.8 系统UUID（稳定获取）
        uuid = "未知"
        # 方案1：dmi product_uuid
        uuid_cmd1 = 'cat /sys/class/dmi/id/product_uuid 2>/dev/null'
        uuid_output1 = execute_cmd(uuid_cmd1)
        if uuid_output1:
            uuid = uuid_output1.upper()
        # 方案2：blkid（备用）
        else:
            uuid_cmd2 = f'blkid /dev/{dev_name}1 2>/dev/null | grep "UUID" | cut -d= -f2 | sed "s/\"//g"'
            uuid_output2 = execute_cmd(uuid_cmd2)
            if uuid_output2:
                uuid = uuid_output2.upper()
        result["system_uuid"] = uuid

    # ========== 3. 其他系统 ==========
    else:
        for k in result.keys():
            result[k] = f"暂不支持{platform.system()}系统" if k != "os" else platform.system()
        return result

    # ========== 4. 设备唯一标识（终极兜底方案） ==========
    unique_parts = []
    # 优先：系统UUID（最稳定）
    if result["system_uuid"] != "未知":
        unique_parts.append(result["system_uuid"])
    # 其次：主板序列号
    if result["motherboard_serial"] != "未知":
        unique_parts.append(result["motherboard_serial"])
    # 最后：硬盘序列号（兜底）
    if result["disk_serial"] != "未知":
        unique_parts.append(result["disk_serial"].replace("卷序列号-", ""))

    # if unique_parts:
    #     result["device_unique_id"] = "_".join(unique_parts)
    # else:
    #     result["device_unique_id"] = "无法生成唯一标识"

    return result



