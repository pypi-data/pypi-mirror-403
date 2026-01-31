import logging
import sys
from ..config_utils import ConfigUtils
from .proxy_class import ProxyClass
from .proxy_config import ProxyConfig

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False  # 核心：禁止日志向上传递到根logger（避免重复输出）
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    style='%'  # 显式指定格式风格，避免版本兼容问题
)
handler.setFormatter(formatter)
logger.addHandler(handler)
#从config.ini中读取配置
_config_parser = ConfigUtils.initConfig('config.ini')
proxy_api_url = ConfigUtils.get_config_value(_config_parser,'proxy', 'api_url', '')
proxy_config = ProxyConfig()
proxy_config.set_threshold(10)
proxy_config.use_redis = False
proxy_config.set_get_time(3)
proxy_config.set_api_url(proxy_api_url)
# 创建全局单例实例（只会创建一次）
proxy_class = ProxyClass(proxy_config, logger)

def get_proxy_tool():
    """获取代理工具（返回全局单例）"""
    return proxy_class  # 直接返回全局单例，不再创建新实例