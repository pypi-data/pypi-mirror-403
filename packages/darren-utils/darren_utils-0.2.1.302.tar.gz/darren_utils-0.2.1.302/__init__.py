# darren_utils/__init__.py
"""
darren_utils 对外统一入口。
这里集中导出常用的顶层对象，方便用户直接：
"""

# 线程池
from .ThreadPool import DarrenThreadPool

# 云端网络功能
from .fn_net_work import FNNetWork

# 代理相关工具
from .proxy.common_proxy import get_proxy_tool
from .proxy.proxy_class import ProxyClass
from .proxy.proxy_config import ProxyConfig
from .Proxy_tools import BaseProxyTools

# HTTP 客户端封装
from .darren_http_class import DarrenHttp, DarrenHttpSession

# 原有 darren 入口（时间/字符串/加解密等工具）
from . import darren_module as darren


__all__ = [
    # 主入口
    'darren',

    # 线程池
    'DarrenThreadPool',

    # 网络功能
    'FNNetWork',

    # 代理相关
    'get_proxy_tool',
    'ProxyClass',
    'ProxyConfig',
    'BaseProxyTools',

    # HTTP 客户端
    'DarrenHttp',
    'DarrenHttpSession',
]

# darren 模块已通过包外的 darren.py 包装器支持直接导入
