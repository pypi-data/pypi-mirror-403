
class RedisInfo:
    def __init__(self, host="localhost", port=6379, password=""):
        self.host = host
        self.port = port
        self.password = password


try:
    import redis
    use_redis = True
except ImportError:
    use_redis = False
    redis = None
class ProxyConfig:
    def __init__(self,redis_info=RedisInfo()):
        # Redis配置
        if use_redis:
            self.redis_client = redis.Redis(host=redis_info.host, port=redis_info.port, password=redis_info.password)
        else:
            self.redis_client = None
        self.threshold = 5#代理IP阈值
        self.check_url = "http://httpbin.org/ip"#验证地址
        self.timeout = 5#请求超时时间
        self.verify_proxy = True#是否验证代理IP的可用性开关
        self.ttl = 30#代理IP的存活时间
        self.api_url = ""
        self.verify_thread_num=10#验证代理IP的线程数
        self.get_time=3#获取代理IP的间隔时间(指的是从api获取代理IP的间隔时间)
        self.use_redis = use_redis  # 是否使用Redis模式，如果Redis不可用则默认为False
        self.redis_prefix="myapp"#redis前缀
        # 初始化Redis连接（如果启用）
        if self.use_redis:
            self.redis_client = self.redis_client
        else:
            self.redis_client = None
    def set_threshold(self, threshold=5):
        """
        设置代理IP阈值
        :param threshold: 代理IP阈值
        :return: None
        """
        self.threshold = threshold
    def set_get_time(self, get_time=3):
        """
        设置获取代理IP的间隔时间
        :param get_time: 获取代理IP的间隔时间
        :return: None
        """
        self.get_time = get_time
    def set_redis_prefix(self, redis_prefix="myapp"):
        """
        设置redis前缀
        :param redis_prefix: redis前缀
        :return: None
        """
        self.redis_prefix = redis_prefix
    def set_check_url(self, check_url="http://httpbin.org/ip"):
        """
        设置验证地址
        :param check_url: 验证地址
        :return: None
        """
        self.check_url = check_url
    def set_timeout(self, timeout=5):
        """
        设置请求超时时间
        :param timeout: 请求超时时间
        :return: None
        """
        self.timeout = timeout
    def set_verify_proxy(self, verify_proxy=True):
        """
        设置是否验证代理IP的开关
        :param verify_proxy: 是否验证代理IP的开关
        :return: None
        """
        self.verify_proxy = verify_proxy
    def set_ttl(self, ttl=30):
        """
        设置代理IP的存活时间
        :param ttl: 代理IP的存活时间
        :return: None
        """
        self.ttl = ttl
    def set_api_url(self, api_url="http://your-proxy-api.com"):
        """
        设置代理API地址
        :param api_url: 代理API地址
        :return: None
        """
        self.api_url = api_url
    def set_verify_thread_num(self, verify_thread_num=10):
        """
        设置验证代理IP的线程数
        :param verify_thread_num: 验证代理IP的线程数
        :return: None
        """
        self.verify_thread_num = verify_thread_num