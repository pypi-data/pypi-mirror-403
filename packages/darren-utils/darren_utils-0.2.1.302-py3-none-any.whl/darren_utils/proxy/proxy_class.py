import logging
import re
import threading
import time

import requests
import concurrent.futures

from ..Proxy_tools import BaseProxyTools

ip_pattern = r'(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})'

# 全局代理池和锁，用于在所有实例间共享
_global_proxy_pool = []
_global_proxy_pool_lock = threading.Lock()

# 全局获取锁和状态，确保所有实例共享
_global_fetch_lock = threading.Lock()
_global_fetching_lock = threading.Lock()
_global_is_fetching = False
_global_last_fetch_time = None

class ProxyClass(BaseProxyTools):
    # 单例实例
    _instance = None
    _instance_lock = threading.Lock()
    
    def __new__(cls, proxy_config=None, logger=None):
        """单例模式：确保只有一个实例"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, proxy_config, logger=None):
        """初始化（单例模式下只会执行一次）"""
        # 避免重复初始化
        if self._initialized:
            return
        
        self.proxy_config = proxy_config
        self.logger = logger or logging.getLogger(__name__)
        
        # 全局代理池和锁，用于在所有实例间共享
        global _global_proxy_pool, _global_proxy_pool_lock
        global _global_fetch_lock, _global_fetching_lock
        
        self.proxy_pool = _global_proxy_pool
        self.proxy_pool_lock = _global_proxy_pool_lock
        
        if self.proxy_config.use_redis and self.proxy_config.redis_client:
            self.redis_client = self.proxy_config.redis_client
            self.redis_prefix = self.proxy_config.redis_prefix
            self.ttl = self.proxy_config.ttl
        else:
            self.redis_client = None
            self.redis_prefix = None
            self.ttl = self.proxy_config.ttl
        
        # 使用全局锁，确保所有线程共享
        self.fetch_lock = _global_fetch_lock
        self.fetching_lock = _global_fetching_lock
        
        # 添加stats锁
        self.stats_lock = threading.Lock()
        
        self.stats = {
            '总数量': 0,  # 所有代理IP的总数量
            '可使用数量': 0,  # 可以立即使用的有效代理IP数量
            '等待验证': 0,  # 等待验证的代理数量
            '验证失败': 0,  # 验证失败的代理数量
            '正在验证': 0,  # 正在验证中的代理数量
            '已取数量': 0,  # 已从池中取走的代理数量
            'api获取数量': 0,  # 从API添加到池中的代理数量
            '失效数量': 0  # 失效的代理IP数量
        }
        
        # 标记为已初始化
        self._initialized = True
        self.logger.info("✓ ProxyClass 单例实例已初始化")

    def get_one_proxy(self, timeout=-1):  # 获取一个代理IP，支持超时参数
        # 立即尝试获取（只检查一次）
        self.check_proxy_list_num_async()
        proxy = self._get_proxy_from_pool_direct()  # 使用直接获取方法，避免重复检查
        if proxy:
            # 使用stats锁保护统计更新
            with self.stats_lock:
                self.stats['已取数量'] += 1
                self.stats['可使用数量'] -= 1
            self.logger.debug(f"获取代理成功：{proxy}")


            return {
                    'http': f"http://{proxy}",
                    'https': f"http://{proxy}"
                }

        # 无限等待模式
        if timeout == -1:
            while not (proxy := self._get_proxy_from_pool_direct()):
                time.sleep(0.5)  # 增加等待时间，减少循环频率
            # 使用stats锁保护统计更新
            with self.stats_lock:
                self.stats['已取数量'] += 1
                self.stats['可使用数量'] -= 1
            self.logger.debug(f"获取代理成功：{proxy}")
            return {
                    'http': f"http://{proxy}",
                    'https': f"http://{proxy}"
                }

        # 有限超时或无超时模式
        start_time = time.time()
        while timeout is not None and time.time() - start_time < timeout:
            if proxy := self._get_proxy_from_pool_direct():
                # 使用stats锁保护统计更新
                with self.stats_lock:
                    self.stats['已取数量'] += 1
                    self.stats['可使用数量'] -= 1
                self.logger.debug(f"获取代理成功：{proxy}")
                return {
                    'http': f"http://{proxy}",
                    'https': f"http://{proxy}"
                }
            time.sleep(0.5)  # 增加等待时间，减少循环频率

        return None

    def _check_proxy_threshold(self):
        pool_size=0
        """检查代理池数量是否低于阈值，如是则启动获取"""
        if self.redis_client and self.redis_prefix:
            # Redis模式
            pool_key = f"{self.redis_prefix}:proxy_pool"
            pool_size = self.redis_client.scard(pool_key)
        else:
            # 内存模式
            with self.proxy_pool_lock:
                pool_size = len(self.proxy_pool)
        if pool_size < self.proxy_config.threshold:

            # 检查是否已经在获取中
            if not self.is_fetching:
                self.check_proxy_list_num_async()

    def _get_proxy_from_pool(self):
        """从代理池中获取一个代理（带检查）"""
        self.check_proxy_list_num_async()
        return self._get_proxy_from_pool_direct()
    
    def _get_proxy_from_pool_direct(self):
        """从代理池中直接获取一个代理（不检查数量）"""
        if self.redis_client and self.redis_prefix:
            pool_key = f"{self.redis_prefix}:proxy_pool"
            # 使用spop直接弹出一个代理，更高效
            proxy_bytes = self.redis_client.spop(pool_key)
            if proxy_bytes:
                proxy = proxy_bytes.decode('utf-8')
                proxy_key = f"{self.redis_prefix}:proxy:{proxy}"
                # 检查代理键是否仍然存在（未过期）
                if self.redis_client.exists(proxy_key):
                    return proxy
            return None
        else:
            # 内存模式
            with self.proxy_pool_lock:
                if self.proxy_pool:
                    proxy = self.proxy_pool.pop(0)
                    return proxy
            return None

    def add_proxy(self, proxy):
        """
        添加代理IP到代理池
        :param proxy: 代理IP
        :return: None
        """
        if self.redis_client and self.redis_prefix:
            # Redis模式 - 使用独立键存储每个代理IP
            proxy_key = f"{self.redis_prefix}:proxy:{proxy}"
            pool_key = f"{self.redis_prefix}:proxy_pool"

            # 设置代理IP的值，并设置独立TTL
            self.redis_client.set(proxy_key, proxy)
            self.redis_client.expire(proxy_key, self.ttl)

            # 将代理IP添加到池集合中（用于快速查询）
            self.redis_client.sadd(pool_key, proxy)
            self.redis_client.expire(pool_key, self.ttl)  # 集合作为备份，设置较长TTL
            with self.stats_lock:
                self.stats['总数量'] += 1
                self.stats['可使用数量'] += 1


            
        else:
            # 内存模式
            with self.proxy_pool_lock:
                if proxy not in self.proxy_pool:
                    self.proxy_pool.append(proxy)
                    with self.stats_lock:
                        self.stats['总数量'] += 1
                        self.stats['可使用数量'] += 1
                    

    def delete_proxy(self, proxy):
        """
        从代理池中删除代理IP
        :param proxy: 代理IP
        :return: None
        """
        if self.redis_client and self.redis_prefix:
            # Redis模式
            proxy_key = f"{self.redis_prefix}:proxy:{proxy}"
            pool_key = f"{self.redis_prefix}:proxy_pool"

            # 删除代理IP的独立键
            self.redis_client.delete(proxy_key)
            # 从池集合中移除代理IP
            self.redis_client.srem(pool_key, proxy)
            with self.stats_lock:
                # 更新统计信息
                self.stats['总数量'] -= 1
                # 重新计算可用数量
                self.stats['可使用数量'] = self.redis_client.scard(pool_key)


        else:
            # 内存模式
            with self.proxy_pool_lock:
                if proxy in self.proxy_pool:
                    self.proxy_pool.remove(proxy)
                    with self.stats_lock:
                        self.stats['总数量'] -= 1
                        self.stats['可使用数量'] = len(self.proxy_pool)



    def clear_proxy(self):
        """
        清空代理池
        :return: None
        """
        if self.redis_client and self.redis_prefix:
            # Redis模式
            pool_key = f"{self.redis_prefix}:proxy_pool"
            # 获取池中所有代理IP
            all_proxies = self.redis_client.smembers(pool_key)
            # 删除所有代理IP的独立键
            for proxy_bytes in all_proxies:
                proxy = proxy_bytes.decode('utf-8')
                proxy_key = f"{self.redis_prefix}:proxy:{proxy}"
                self.redis_client.delete(proxy_key)
            # 删除池集合
            with self.proxy_pool_lock:
                self.redis_client.delete(pool_key)

                # 重置统计信息
                self.stats['总数量'] = 0
                self.stats['可使用数量'] = 0

        else:
            # 内存模式
            with self.proxy_pool_lock:
                self.proxy_pool.clear()
                self.stats['总数量'] = 0
                self.stats['可使用数量'] = 0

    def _verify_proxy(self, proxy):

        """验证代理IP的可用性"""
        try:
            self.logger.debug(f"正在验证代理IP {proxy}")
            with self.stats_lock:
                self.stats['等待验证'] -= 1
                self.stats['正在验证'] += 1

            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(
                self.proxy_config.check_url,
                proxies=proxies,
                timeout=self.proxy_config.timeout
            )
            self.logger.debug(f"验证代理IP {proxy} 成功")
            with self.stats_lock:
                self.stats['正在验证'] -= 1
            
            return response.status_code == 200
        except Exception:
            self.logger.error(f"验证代理IP {proxy} 失败")
            with self.stats_lock:
                self.stats['正在验证'] -= 1
            # stats = self.get_proxy_stats()
            # self.logger.info(stats)
            return False

    def get_proxy_stats(self):  # 获取代理IP统计信息例如 可用的代理IP数量 等待验证的IP数量 验证失败的IP数量 验证中的IP数量 总代理IP数量 已提取的代理IP数量 从API获取的代理IP数量
        return self.stats

    def check_proxy_list_num_async(self):
        """异步检查池中数量是否小于阈值"""
        global _global_is_fetching
        
        # 使用全局获取锁确保只有一个线程能启动获取任务
        if self.fetch_lock.acquire(blocking=False):
            try:
                # 使用全局fetching锁保护全局is_fetching标志
                with self.fetching_lock:
                    # 再次检查是否已经在获取中（使用全局状态）
                    if not _global_is_fetching:
                        _global_is_fetching = True
                        # 创建一个新线程来执行异步任务
                        thread = threading.Thread(target=self._async_fetch_proxies_if_needed)
                        thread.daemon = True
                        thread.start()
            finally:
                self.fetch_lock.release()

    def _async_fetch_proxies_if_needed(self):
        """异步获取代理IP（如果数量不足阈值）"""
        global _global_last_fetch_time
        
        try:
            # 检查上次获取时间，确保满足间隔要求（使用全局时间）
            current_time = time.time()
            if _global_last_fetch_time is not None:
                time_since_last_fetch = current_time - _global_last_fetch_time
                if time_since_last_fetch < self.proxy_config.get_time:
                    self.logger.warning(f"距离上次获取仅 {time_since_last_fetch:.2f} 秒，等待 {self.proxy_config.get_time - time_since_last_fetch:.2f} 秒后再次获取")
                    # 等待到满足获取间隔
                    time.sleep(self.proxy_config.get_time - time_since_last_fetch)
            else:
                self.logger.debug("首次获取代理IP")
            # 初始化检查变量
            need_fetch = False
            if self.redis_client and self.redis_prefix:
                # Redis模式
                pool_key = f"{self.redis_prefix}:proxy_pool"
                pool_size = self.redis_client.scard(pool_key)
                need_fetch = pool_size < self.proxy_config.threshold
            else:
                # 内存模式
                with self.proxy_pool_lock:
                    need_fetch = len(self.proxy_pool) < self.proxy_config.threshold

            if not need_fetch:
                return  # 数量足够，不需要获取新代理
            try:
                # 从API获取代理IP
                response = requests.get(self.proxy_config.api_url)
                if response.status_code == 200:
                    content = response.text
                    # self.logger.info(f"从API获取代理IP成功{content}")
                    # 提取代理IP
                    proxies = re.findall(ip_pattern, content)
                    if len(proxies) > 0:
                        self.logger.info(f"从API获取代理IP成功，获取到 {len(proxies)} 个代理")
                    else:
                        self.logger.warning(f"从API获取代理IP失败:{content}")

                    # 使用stats锁保护统计更新
                    with self.stats_lock:
                        self.stats['api获取数量'] += len(proxies)

                    if self.proxy_config.verify_proxy and proxies:
                        # 使用线程池验证代理IP
                        self._verify_proxies_with_thread_pool(proxies)
                        # 更新全局获取时间
                        _global_last_fetch_time = time.time()
                        self.logger.debug(f"✓ 本次从API获取并验证 {len(proxies)} 个代理IP")
            except Exception as e:
                self.logger.error(f"异步获取代理时出错: {e}")
        finally:
            # 使用全局fetching锁保护全局is_fetching标志
            global _global_is_fetching
            with self.fetching_lock:
                # 重置获取状态
                _global_is_fetching = False

    def _verify_proxies_with_thread_pool(self, proxies):
        """
        使用线程池验证代理IP

        Args:
            proxies: 代理IP列表
        Returns:
            list: 验证通过的代理IP列表
        """
        # 使用线程池执行器进行验证
        with self.stats_lock:
            self.stats['等待验证'] = len(proxies)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.proxy_config.verify_thread_num) as executor:
            # 提交所有验证任务
            future_to_proxy = {executor.submit(self._verify_proxy, proxy): proxy for proxy in proxies}

            valid_proxies = []
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    is_valid = future.result()
                    # self.logger.info(f"验证代理IP {proxy} {is_valid}")
                    if is_valid:

                        self.add_proxy(proxy)

                    else:
                        with self.stats_lock:
                            # 验证失败的代理数量增加
                            #self.stats['等待验证'] -= 1
                            self.stats['验证失败'] += 1

                except Exception as e:
                    with self.stats_lock:
                        self.stats['验证失败'] += 1
                        #self.stats['等待验证'] -= 1

                    self.logger.error(f"验证代理 {proxy} 时出错: {e}")
                # finally:
                #     with self.stats_lock:
                #         # 减少等待验证的数量
                #         self.stats['等待验证'] -= 1


            return valid_proxies

