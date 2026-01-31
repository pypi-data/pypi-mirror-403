import json
import os
import sys
import time
import traceback
import types
from datetime import datetime
from typing import Optional, Dict, Union, Any, Tuple
from functools import wraps
import requests

from MeUtils import MeUtils

try:
    import httpx
    from httpx import HTTPTransport
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    HTTPTransport = None

# 添加父目录到路径（如果不存在）
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.append(_parent_dir)

from Proxy_tools import BaseProxyTools



class HttpMethodDescriptor:
    """描述符类，让方法同时支持实例调用和类调用"""
    def __init__(self, method_name: str):
        self.method_name = method_name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            # 通过类调用，返回静态方法
            def static_method(url: str,
                            proxy_tool: Optional[BaseProxyTools] = None,
                            use_httpx: bool = False,
                            http2: bool = False,
                            enable_detailed_logging: bool = False,
                            **kwargs) -> Optional[Any]:
                return objtype._static_request(
                    method=self.method_name.upper(),
                    url=url,
                    proxy_tool=proxy_tool,
                    use_httpx=use_httpx,
                    http2=http2,
                    enable_detailed_logging=enable_detailed_logging,
                    **kwargs
                )
            return static_method
        else:
            # 通过实例调用，返回绑定方法
            @wraps(obj._get_instance)
            def bound_method(url: str, **kwargs) -> Optional[Any]:
                return obj._get_instance(self.method_name.upper(), url, **kwargs)
            return bound_method


class DarrenHttpSession:
    """
    扩展的HTTP Session类，支持requests和httpx，添加额外功能
    """
    # 类常量
    MAX_LOG_TEXT_LENGTH = 10000  # 日志文本最大长度（10KB）
    LOG_DIR = 'http_logs'  # 日志目录

    def __init__(self, proxy_tool: Optional[BaseProxyTools] = None, 
                 enable_detailed_logging: bool = False,
                 use_httpx: bool = False,
                 http2: bool = False):
        """
        初始化Session
        
        Args:
            proxy_tool: 代理工具实例
            enable_detailed_logging: 是否启用详细日志
            use_httpx: 是否使用httpx库（False则使用requests）
            http2: 是否启用HTTP/2支持（仅httpx有效）
        """
        self.proxy_tool = proxy_tool
        self._cached_proxy = None  # 添加代理缓存
        self._proxy_failed = False  # 标记代理是否失效
        self.enable_detailed_logging = enable_detailed_logging
        self.use_httpx = use_httpx
        self.http2 = http2
        
        if use_httpx:
            if not HTTPX_AVAILABLE:
                raise ImportError("httpx库未安装，请使用 pip install httpx 安装")
            # httpx的代理需要在创建Client时设置，初始时不设置代理
            # 如果后续需要代理，会重新创建Client
            self.session = httpx.Client(follow_redirects=True, http2=http2)
            self._httpx_proxies = None  # 记录当前使用的代理
        else:
            self.session = requests.Session()
        
        self._last_response = None  # 保存最后一次响应，用于getLocation()

    @property
    def cookies(self):
        """
        访问底层session的cookies属性
        
        Returns:
            cookies对象（requests.cookies.RequestsCookieJar 或 httpx.Cookies）
        """
        return self.session.cookies
    def _normalize_cookies(self):
        """
        规范化底层 cookies：
        - 对 httpx.Cookies：遇到同名 cookie 只保留最后一个
        - 对 requests 的 CookiesJar：保持原样（不会抛 CookieConflict）
        """
        cookies_obj = self.session.cookies
        # httpx.Cookies 特征：类名是 'Cookies'，且有 jar 属性
        if type(cookies_obj).__name__ == "Cookies" and hasattr(cookies_obj, "jar"):
            tmp = {}
            for c in cookies_obj.jar:
                tmp[c.name] = c.value  # 同名覆盖，保留最后一个
            # 先清空再重新写入
            cookies_obj.clear()
            for name, value in tmp.items():
                cookies_obj.set(name, value)

    @property
    def headers(self):
        """
        访问底层session的headers属性
        
        Returns:
            headers对象（dict-like）
        """
        return self.session.headers

    def _log_request_details(self, task_id: Optional[str], method: str, url: str,
                             headers: Dict, cookies: Any, proxies: Optional[Dict],
                             request_start: float, response: Optional[Any] = None,
                             error: Optional[Exception] = None,
                             params: Optional[Dict] = None,
                             data: Optional[Any] = None,
                             json_data: Optional[Any] = None,
                             attempt: Optional[int] = None,
                             max_attempts: Optional[int] = None):
        """记录详细请求信息到文件"""
        if not self.enable_detailed_logging:
            return

        # 计算耗时
        duration = time.time() - request_start if request_start else 0
        
        # 确定实际使用的代理（优先使用传入的proxies，否则使用缓存的代理）
        actual_proxy = proxies if proxies else self._cached_proxy
        
        log_data = {
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'library': 'httpx' if self.use_httpx else 'requests',
            'request': {
                'method': method,
                'url': url,
                'headers': dict(headers) if headers else {},
                'cookies': cookies,
                'proxies': proxies,  # 传入的代理配置
                'used_proxy': actual_proxy,  # 实际使用的代理
                'params': params,
                'data': data,
                'json': json_data
            },
            'performance': {
                'duration_ms': round(duration * 1000, 2)  # 毫秒，保留2位小数
            }
        }
        
        # 添加重试信息
        if attempt is not None:
            log_data['attempt'] = {
                'current': attempt + 1,  # 第几次尝试（从1开始）
                'max': max_attempts if max_attempts else None,
                'is_retry': attempt > 0  # 是否是重试
            }

        if response:
            # 提取公共的响应信息（httpx和requests通用）
            content_type = response.headers.get('content-type', '').lower()
            response_url = str(response.url) if self.use_httpx else response.url
            
            log_data['response'] = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content_length': len(response.content) if response.content else 0,
                'content_type': response.headers.get('content-type', ''),
                'url': response_url
            }
            
            if 'text/' in content_type:
                try:
                    # 限制日志文本长度，避免日志文件过大
                    text_content = response.text
                    if len(text_content) > self.MAX_LOG_TEXT_LENGTH:
                        log_data['response']['text'] = text_content[:self.MAX_LOG_TEXT_LENGTH] + f'...[截断，总长度: {len(text_content)}]'
                    else:
                        log_data['response']['text'] = text_content
                except (UnicodeDecodeError, AttributeError, LookupError) as e:
                    log_data['response']['text'] = f'[无法解码文本: {type(e).__name__}]'
            elif 'application/json' in content_type:
                try:
                    # httpx和requests的json()方法调用方式相同
                    log_data['response']['json'] = response.json()
                except (ValueError, requests.JSONDecodeError, AttributeError) as e:
                    try:
                        text_content = response.text
                        if len(text_content) > self.MAX_LOG_TEXT_LENGTH:
                            log_data['response']['text'] = text_content[:self.MAX_LOG_TEXT_LENGTH] + f'...[截断，总长度: {len(text_content)}]'
                        else:
                            log_data['response']['text'] = text_content
                    except (UnicodeDecodeError, AttributeError, LookupError) as e2:
                        log_data['response']['text'] = f'[无法解码文本: {type(e2).__name__}]'
        elif error:
            log_data['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            }

        # 保存到文件
        try:
            log_dir = self.LOG_DIR
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 日志文件名直接使用task_id，如果没有task_id则使用默认值
            if task_id:
                filename = f"{log_dir}/{task_id}.txt"
            else:
                filename = f"{log_dir}/request_log_default_{datetime.now().strftime('%Y%m%d')}.txt"
            
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False, indent=2) + '\n\n')
        except (OSError, IOError, PermissionError) as e:
            # 日志写入失败不应该影响主流程，只打印警告
            print(f"警告: 日志写入失败: {type(e).__name__}: {e}")

    def request(self, method: str, url: str, headers: Optional[Dict] = None,
                cookies: Optional[Union[Dict, str]] = None, 
                proxies: Optional[Dict] = None,
                use_proxy: bool = False, 
                max_retries: int = 3, 
                timeout: Union[int, Tuple[int, int], float] = 10,
                task_id: Optional[str] = None,
                allow_redirects: bool = True,
                params: Optional[Dict] = None,
                data: Optional[Any] = None,
                json: Optional[Any] = None,
                **kwargs) -> Optional[Any]:
        """
        发送HTTP请求，支持重试和代理

        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            cookies: Cookie字典或字符串
            proxies: 代理配置
            use_proxy: 是否使用代理
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            task_id: 请求id
            allow_redirects: 是否允许重定向（requests参数，httpx使用follow_redirects）
            params: URL参数
            data: 请求体数据
            json: JSON数据
            **kwargs: 其他传递给requests/httpx的参数

        Returns:
            Response对象，失败时返回None
        """
        headers = headers or {}
        # 保存原始传入的proxies，用于重试时恢复
        original_proxies = proxies
        current_proxies = proxies

        # 处理httpx和requests的参数差异
        if self.use_httpx:
            # httpx使用follow_redirects而不是allow_redirects
            if 'follow_redirects' not in kwargs:
                kwargs['follow_redirects'] = allow_redirects
            # httpx的timeout需要转换为httpx.Timeout对象
            if 'timeout' not in kwargs and timeout:
                try:
                    if isinstance(timeout, (int, float)) and timeout > 0:
                        kwargs['timeout'] = httpx.Timeout(timeout)
                    elif isinstance(timeout, tuple) and len(timeout) > 0:
                        connect_timeout = timeout[1] if len(timeout) > 1 and timeout[1] > 0 else timeout[0]
                        if timeout[0] > 0:
                            kwargs['timeout'] = httpx.Timeout(timeout[0], connect=connect_timeout)
                except (TypeError, ValueError) as e:
                    # 如果timeout转换失败，使用默认值
                    print(f"警告: timeout参数无效，使用默认值: {e}")
                    kwargs['timeout'] = httpx.Timeout(10.0)
        else:
            # requests使用allow_redirects
            if 'allow_redirects' not in kwargs:
                kwargs['allow_redirects'] = allow_redirects

        for attempt in range(max_retries + 1):
            # 每次重试时记录开始时间（用于计算本次请求的耗时）
            request_start = time.time() if self.enable_detailed_logging else None
            # 每次重试时，优先使用原始传入的proxies参数（如果存在）
            # 注意：只在第一次尝试或重试时如果current_proxies被清空时才恢复
            if original_proxies and not current_proxies:
                current_proxies = original_proxies
            # 如果启用了代理但没有有效的代理配置，则使用缓存或获取新代理
            elif use_proxy and not current_proxies:
                if self._cached_proxy and not self._proxy_failed:
                    # 使用缓存的代理
                    current_proxies = self._cached_proxy
                elif self.proxy_tool:
                    # 获取新代理并缓存
                    try:
                        proxy_result = self.proxy_tool.get_one_proxy()
                        if proxy_result:
                            current_proxies = proxy_result
                            self._cached_proxy = proxy_result
                            self._proxy_failed = False  # 重置失败标记
                    except Exception as e:
                        # 代理获取失败，记录但不中断流程
                        if attempt < max_retries:
                            print(f"警告: 获取代理失败: {type(e).__name__}: {e}")
                        current_proxies = None

            try:
                if isinstance(cookies, str):
                    cookies = MeUtils.cookie_string_to_dict(cookies)


                # 构建请求参数，先从kwargs中移除proxies（如果存在），避免冲突
                # 因为我们需要统一处理代理参数（httpx和requests格式不同）
                request_kwargs = {
                    'method': method,
                    'url': url,
                    'headers': headers,
                }
                
                # 复制kwargs，但排除proxies和proxy（我们会单独处理）
                # 使用字典推导式简化代码
                request_kwargs.update({
                    k: v for k, v in kwargs.items() 
                    if k not in ('proxies', 'proxy')
                })
                
                # 处理timeout（如果已经在kwargs中处理过，则不再添加）
                # 注意：httpx的timeout已经在上面处理过了，这里只处理requests的情况
                if 'timeout' not in request_kwargs and not self.use_httpx:
                    request_kwargs['timeout'] = timeout
                
                # 添加cookies
                if cookies:
                    request_kwargs['cookies'] = cookies
                
                # 添加代理（处理httpx和requests的差异）
                if current_proxies:
                    if self.use_httpx:
                        # httpx的代理必须在创建Client时设置，不能通过request参数传入
                        # 转换代理格式：从requests格式 {"http": "...", "https": "..."}
                        # 转换为httpx格式 {"http://": "...", "https://": "..."}
                        httpx_proxies = {
                            f'{protocol}://': current_proxies[protocol]
                            for protocol in ('http', 'https')
                            if current_proxies.get(protocol)
                        }
                        
                        # 如果代理发生变化，需要重新创建Client
                        # 注意：空字典{}和None都表示没有代理，需要统一处理
                        current_proxy_state = httpx_proxies if httpx_proxies else None
                        cached_proxy_state = self._httpx_proxies if self._httpx_proxies else None
                        if current_proxy_state != cached_proxy_state:
                            # 保存旧Client的状态（cookies、headers等）
                            old_cookies = None
                            old_headers = None
                            if self.use_httpx and HTTPX_AVAILABLE and isinstance(self.session, httpx.Client):
                                # 保存cookies和headers
                                try:
                                    old_cookies = dict(self.session.cookies)
                                except (AttributeError, TypeError):
                                    pass
                                try:
                                    old_headers = dict(self.session.headers)
                                except (AttributeError, TypeError):
                                    pass
                            
                            # 关闭旧的Client
                            try:
                                self.session.close()
                            except (AttributeError, RuntimeError, Exception):
                                # 忽略关闭时的异常，不影响主流程
                                pass
                            
                            # 创建新的Client，设置代理
                            # httpx官方方式：使用mounts参数配合HTTPTransport(proxy=...)
                            # 参考：https://www.python-httpx.org/advanced/#http-transports
                            if not HTTPX_AVAILABLE or HTTPTransport is None:
                                raise ImportError("httpx库未安装或版本不支持HTTPTransport")
                            
                            # 构建mounts（如果有代理）
                            # 使用字典推导式简化代码
                            mounts = {
                                protocol: HTTPTransport(proxy=httpx_proxies[protocol])
                                for protocol in ('http://', 'https://')
                                if httpx_proxies.get(protocol)
                            }
                            # 如果没有mounts，设置为None
                            mounts = mounts if mounts else None
                            
                            # 创建新的Client
                            self.session = httpx.Client(
                                mounts=mounts,
                                follow_redirects=True,
                                http2=self.http2
                            )
                            
                            # 恢复旧Client的状态
                            if old_cookies:
                                self.session.cookies.update(old_cookies)
                            if old_headers:
                                self.session.headers.update(old_headers)
                            
                            # 保存当前代理状态（统一处理空字典和None）
                            self._httpx_proxies = httpx_proxies if httpx_proxies else None
                        # httpx不需要在request_kwargs中添加代理参数
                    else:
                        # requests使用proxies（复数）参数，字典格式，可以在request时传入
                        request_kwargs['proxies'] = current_proxies
                
                # 添加params, data, json（只添加非None的值）
                if params:
                    request_kwargs['params'] = params
                if data is not None:
                    request_kwargs['data'] = data
                if json is not None:
                    request_kwargs['json'] = json

                # 发送请求（httpx和requests的调用方式相同）
                response = self.session.request(**request_kwargs)
                
                self._last_response = response

                self._normalize_cookies()
                
                # 将 getLocation 方法绑定到 response 对象上
                def getLocation_func(self) -> Optional[str]:
                    """获取本次请求的重定向地址"""
                    # self 就是 response 对象本身
                    try:
                        # 首先尝试从响应头获取Location（适用于禁用重定向的情况）
                        location = self.headers.get('Location') or self.headers.get('location')
                        if location:
                            return location
                        return None
                    except (AttributeError, TypeError, KeyError):
                        return None
                
                # 绑定方法到 response 对象
                response.getLocation = types.MethodType(getLocation_func, response)
                
                # 记录日志（每次请求都记录，包括重试）
                if self.enable_detailed_logging and request_start:
                    self._log_request_details(
                        task_id=task_id,
                        method=method,
                        url=url,
                        headers=headers,
                        cookies=cookies,
                        proxies=current_proxies,
                        request_start=request_start,
                        response=response,
                        params=params,
                        data=data,
                        json_data=json,
                        attempt=attempt,
                        max_attempts=max_retries + 1
                    )
                return response
                
            except Exception as e:
                #traceback.print_exc()
                # 记录日志（每次失败都记录，包括重试）
                if self.enable_detailed_logging and request_start:
                    self._log_request_details(
                        task_id=task_id,
                        method=method,
                        url=url,
                        headers=headers,
                        cookies=cookies,
                        proxies=current_proxies,
                        request_start=request_start,
                        error=e,
                        params=params,
                        data=data,
                        json_data=json,
                        attempt=attempt,
                        max_attempts=max_retries + 1
                    )
                if attempt < max_retries:
                    print(f"第 {attempt + 1} 次请求失败: {type(e).__name__}: {e}，正在重试...")
                    self._proxy_failed = True
                    # 如果使用的是代理工具获取的代理，则清除缓存以便下次获取新代理
                    # 但如果使用的是传入的proxies参数，则保留（下次重试时仍使用）
                    if not original_proxies:
                        current_proxies = None
                else:
                    print(f"请求最终失败: {type(e).__name__}: {e}")
                    return None

        return None

    def get(self, url: str, **kwargs) -> Optional[Any]:
        """发送GET请求"""
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs) -> Optional[Any]:
        """发送POST请求"""
        return self.request('POST', url, **kwargs)

    def put(self, url: str, **kwargs) -> Optional[Any]:
        """发送PUT请求"""
        return self.request('PUT', url, **kwargs)

    def delete(self, url: str, **kwargs) -> Optional[Any]:
        """发送DELETE请求"""
        return self.request('DELETE', url, **kwargs)

    def head(self, url: str, **kwargs) -> Optional[Any]:
        """发送HEAD请求"""
        return self.request('HEAD', url, **kwargs)

    def options(self, url: str, **kwargs) -> Optional[Any]:
        """发送OPTIONS请求"""
        return self.request('OPTIONS', url, **kwargs)

    def patch(self, url: str, **kwargs) -> Optional[Any]:
        """发送PATCH请求"""
        return self.request('PATCH', url, **kwargs)

    def getLocation(self) -> Optional[str]:
        """
        获取最后一次请求的重定向地址
        
        Returns:
            重定向后的URL，如果没有重定向或没有响应则返回None
        """
        if not self._last_response:
            return None
        
        try:
            # 首先尝试从响应头获取Location（适用于禁用重定向的情况）
            location = self._last_response.headers.get('Location') or self._last_response.headers.get('location')
            if location:
                return location
            return None

        except (AttributeError, TypeError, KeyError) as e:
            # 如果获取URL失败，返回None
            return None

    def clear_proxy_cache(self):
        """清除代理缓存"""
        self._cached_proxy = None
        self._proxy_failed = False

    def close(self):
        """关闭session"""
        try:
            if hasattr(self.session, 'close'):
                self.session.close()
        except Exception as e:
            # 关闭失败不应该抛出异常，只记录警告
            print(f"警告: 关闭session失败: {type(e).__name__}: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


class DarrenHttp:
    """
    基于requests/httpx的HTTP客户端封装类，支持Session和非Session模式
    """

    def __init__(self, proxy_tool: Optional[BaseProxyTools] = None, 
                 use_httpx: bool = False,
                 enable_detailed_logging: bool = False,
                 http2: bool = False):
        """
        初始化DarrenHttp客户端

        Args:
            proxy_tool: 代理工具实例
            use_httpx: 是否使用httpx库
            enable_detailed_logging: 是否启用详细日志（非Session模式）
            http2: 是否启用HTTP/2支持（仅httpx有效）
        """
        self.proxy_tool = proxy_tool
        self.use_httpx = use_httpx
        self.enable_detailed_logging = enable_detailed_logging
        self.http2 = http2

    @staticmethod
    def Session(proxy_tool: Optional[BaseProxyTools] = None, 
                enable_detailed_logging: bool = False,
                use_httpx: bool = False,
                http2: bool = False):
        """
        返回扩展的Session对象
        
        Args:
            proxy_tool: 代理工具实例
            enable_detailed_logging: 是否启用详细日志
            use_httpx: 是否使用httpx库
            http2: 是否启用HTTP/2支持（仅httpx有效）
        
        Returns:
            DarrenHttpSession实例
        """
        return DarrenHttpSession(proxy_tool, enable_detailed_logging, use_httpx, http2)

    @staticmethod
    def _static_request(method: str, url: str,
                       proxy_tool: Optional[BaseProxyTools] = None,
                       use_httpx: bool = False,
                       http2: bool = False,
                       enable_detailed_logging: bool = False,
                       **kwargs) -> Optional[Any]:
        """
        静态方法：发送HTTP请求（无需实例化）
        
        Args:
            method: HTTP方法
            url: 请求URL
            proxy_tool: 代理工具实例
            use_httpx: 是否使用httpx库
            http2: 是否启用HTTP/2支持（仅httpx有效）
            enable_detailed_logging: 是否启用详细日志
            **kwargs: 其他请求参数（同Session.request）
        
        Returns:
            Response对象，失败时返回None
        """
        # 创建临时session
        session = DarrenHttpSession(
            proxy_tool=proxy_tool,
            enable_detailed_logging=enable_detailed_logging,
            use_httpx=use_httpx,
            http2=http2
        )
        
        try:
            response = session.request(
                method=method,
                url=url,
                **kwargs
            )
            
            # 如果响应存在，添加 getLocation 方法到 response 对象
            if response:
                # 从 session 获取重定向地址（在关闭 session 前获取）
                location = session.getLocation()
                
                # 将 getLocation 方法添加到 response 对象
                def getLocation_func(self) -> Optional[str]:
                    """获取重定向地址"""
                    return location
                
                # 绑定方法到 response 对象
                response.getLocation = types.MethodType(getLocation_func, response)
            
            return response
        finally:
            session.close()

    def _make_request(self, method: str, url: str, 
                     headers: Optional[Dict] = None,
                     cookies: Optional[Union[Dict, str]] = None, 
                     proxies: Optional[Dict] = None,
                     use_proxy: bool = False, 
                     max_retries: int = 3, 
                     timeout: Union[int, Tuple[int, int], float] = 10,
                     task_id: Optional[str] = None,
                     allow_redirects: bool = True,
                     params: Optional[Dict] = None,
                     data: Optional[Any] = None,
                     json: Optional[Any] = None,
                     enable_detailed_logging: Optional[bool] = None,
                     **kwargs) -> Optional[Any]:
        """
        发送HTTP请求（非Session模式）
        """
        # 如果未指定，使用实例的默认值
        if enable_detailed_logging is None:
            enable_detailed_logging = self.enable_detailed_logging
        
        # 创建临时session
        session = DarrenHttpSession(
            proxy_tool=self.proxy_tool,
            enable_detailed_logging=enable_detailed_logging,
            use_httpx=self.use_httpx,
            http2=self.http2
        )
        
        try:
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                cookies=cookies,
                proxies=proxies,
                use_proxy=use_proxy,
                max_retries=max_retries,
                timeout=timeout,
                task_id=task_id,
                allow_redirects=allow_redirects,
                params=params,
                data=data,
                json=json,
                **kwargs
            )
            return response
        finally:
            session.close()

    def request(self, method: str, url: str, **kwargs) -> Optional[Any]:
        """
        发送HTTP请求（实例方法）

        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他参数（同Session.request）

        Returns:
            Response对象，失败时返回None
        """
        return self._make_request(method, url, **kwargs)

    @staticmethod
    def request_static(method: str, url: str, 
                      proxy_tool: Optional[BaseProxyTools] = None,
                      use_httpx: bool = False,
                      http2: bool = False,
                      enable_detailed_logging: bool = False,
                      **kwargs) -> Optional[Any]:
        """
        发送HTTP请求（静态方法，可直接通过类调用）

        Args:
            method: HTTP方法
            url: 请求URL
            proxy_tool: 代理工具实例
            use_httpx: 是否使用httpx库
            http2: 是否启用HTTP/2支持（仅httpx有效）
            enable_detailed_logging: 是否启用详细日志
            **kwargs: 其他参数（同Session.request）

        Returns:
            Response对象，失败时返回None
        """
        return DarrenHttp._static_request(
            method=method,
            url=url,
            proxy_tool=proxy_tool,
            use_httpx=use_httpx,
            http2=http2,
            enable_detailed_logging=enable_detailed_logging,
            **kwargs
        )

    def _get_instance(self, method: str, url: str, **kwargs) -> Optional[Any]:
        """实例方法内部实现"""
        return self._make_request(method, url, **kwargs)

    # 使用描述符，让方法同时支持实例调用和类调用
    get = HttpMethodDescriptor('get')
    post = HttpMethodDescriptor('post')
    put = HttpMethodDescriptor('put')
    delete = HttpMethodDescriptor('delete')
    head = HttpMethodDescriptor('head')
    options = HttpMethodDescriptor('options')
    patch = HttpMethodDescriptor('patch')

    def close(self):
        """关闭（非Session模式无需关闭）"""
        pass

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


if __name__ == '__main__':
    proxy = {"http": "http://119.102.46.226:40009", "https": "http://119.102.46.226:40009"}
    # 测试Session模式（启用HTTP/2）
    session = DarrenHttp.Session(
        enable_detailed_logging=True,
        use_httpx=True,
        http2=True  # 启用HTTP/2支持
    )
    response = session.request('GET', 'http://utils.darren8.com//ip/getIP', task_id='123', allow_redirects=False, proxies=None,use_proxy= False,timeout=5)
    if response:
        print(f"状态码: {response.status_code}")
        print(f"重定向地址: {session.getLocation()}")
        print(response.text)
    session.close()
    #
    # # 测试非Session模式（启用HTTP/2）
    # http_client = DarrenHttp(use_httpx=True, http2=True)
    # response = http_client.get('https://www.baidu.com', task_id='456')
    # if response:
    #     print(f"状态码: {response.status_code}")
    #
    # # 测试静态方法调用（无需实例化）
    # get_response = DarrenHttp.get('https://www.baidu.com', task_id='456', use_httpx=True, http2=True)
    # if get_response:
    #     print(f"GET静态调用状态码: {get_response.status_code}")

    
    # post_response = DarrenHttp.get('http://www.baiu.com', task_id='456', use_httpx=True, http2=True,allow_redirects=False, proxies=proxy)
    # if post_response:
    #     print(f"POST静态调用状态码: {post_response.status_code}")
    #     print(post_response.getLocation())




