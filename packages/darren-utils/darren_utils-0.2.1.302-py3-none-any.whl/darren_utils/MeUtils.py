import datetime
import json
import os
import re
import urllib
from typing import Dict, Union, Any, Callable, cast
from urllib.parse import urlparse, parse_qs

import requests


class MeUtils:
    @staticmethod
    def is_empty(value: Any) -> bool:
        """
        判断值是否为空

        判断规则：
        - None 为空
        - 空字符串 "" 为空
        - 空列表 [] 为空
        - 空字典 {} 为空
        - 空元组 () 为空
        - 空集合 set() 为空
        - 其他假值（False, 0, 0.0）也为空

        Args:
            value: 要判断的值

        Returns:
            bool: 如果为空返回 True，否则返回 False

        Examples:
            >>> MeUtils.is_empty(None)
            True
            >>> MeUtils.is_empty("")
            True
            >>> MeUtils.is_empty([])
            True
            >>> MeUtils.is_empty({})
            True
            >>> MeUtils.is_empty("hello")
            False
            >>> MeUtils.is_empty([1, 2, 3])
            False
            >>> MeUtils.is_empty({"key": "value"})
            False
        """
        if value is None:
            return True

        # 判断字符串
        if isinstance(value, str):
            return len(value.strip()) == 0

        # 判断列表、元组、集合
        if isinstance(value, (list, tuple, set)):
            return len(value) == 0

        # 判断字典
        if isinstance(value, dict):
            return len(value) == 0

        # 判断其他假值
        if value is False:
            return True

        # 数字 0 和 0.0 视为空
        if isinstance(value, (int, float)) and value == 0:
            return True

        return False

    @staticmethod
    def is_not_empty(value: Any) -> bool:
        """
        判断值是否不为空（is_empty 的反向判断）

        Args:
            value: 要判断的值

        Returns:
            bool: 如果不为空返回 True，否则返回 False

        Examples:
            >>> MeUtils.is_not_empty("hello")
            True
            >>> MeUtils.is_not_empty([1, 2, 3])
            True
            >>> MeUtils.is_not_empty(None)
            False
            >>> MeUtils.is_not_empty("")
            False
        """
        return not MeUtils.is_empty(value)
    @staticmethod
    def get_sms_code(text: str, code_length: int = 6) -> str:
        pattern = rf"\d{{{code_length}}}"
        match_results = re.findall(pattern, text)
        if match_results:
            return match_results[0]
        else:
            return ""
    @staticmethod
    def url_encode(text, is_utf8=True):
        """
        将字符串转换为URL编码

        Args:
            text (str): 要编码的字符串
            is_utf8 (bool): 是否使用UTF-8编码，默认为True

        Returns:
            str: URL编码后的字符串
        """
        if not isinstance(text, str):
            raise ValueError("输入必须是字符串类型")

        if is_utf8:
            # 使用UTF-8编码
            return urllib.parse.quote(text, encoding='utf-8')
        else:
            # 使用系统默认编码
            return urllib.parse.quote(text, encoding='GBK')

    @staticmethod
    def url_get_param(url, param_name):
        """
        从URL中获取指定参数的值

        Args:
            url (str): 完整的URL地址
            param_name (str): 要获取的参数名称

        Returns:
            str: 参数值，如果参数不存在或URL无效则返回空字符串
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)

            # parse_qs返回的是列表，取第一个值
            param_values = query_params.get(param_name)
            if param_values:
                return param_values[0]
            return ""
        except Exception:
            return ""

    @staticmethod
    def url_decode(encoded_text, is_utf8=True):
        """
        将URL编码的字符串解码为原始字符串

        Args:
            encoded_text (str): URL编码的字符串
            is_utf8 (bool): 是否使用UTF-8解码，默认为True

        Returns:
            str: 解码后的原始字符串
        """
        if not isinstance(encoded_text, str):
            raise ValueError("输入必须是字符串类型")

        if is_utf8:
            # 使用UTF-8解码
            return urllib.parse.unquote(encoded_text, encoding='utf-8')
        else:
            # 使用系统默认解码
            return urllib.parse.unquote(encoded_text, encoding='GBK')

    @staticmethod
    def json_get_nested(obj, path, default=""):
        """
        安全获取嵌套属性/键值

        Args:
            obj: 要访问的对象
            path: 键路径，如 "data.uname" 或 ["data", "uname"]
            default: 默认值

        Returns:
            获取到的值或默认值
        """
        if isinstance(path, str):
            keys = path.split(".")
        else:
            keys = path

        current = obj
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    @staticmethod
    def json_parse_safe(obj):
        """安全的JSON处理"""
        try:
            if isinstance(obj, str):
                return json.loads(obj) if obj else {}
            elif isinstance(obj, (dict, list)):
                # 如果已经是 dict 或 list，直接返回
                return obj
            else:
                return {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def _fetch_ip_data(url: str, timeout: int = 10) -> Union[dict, str, None]:
        """
        内部方法：获取IP数据
        
        Args:
            url: 请求URL
            timeout: 超时时间
            
        Returns:
            dict: JSON数据，str: 文本数据，None: 请求失败
        """
        try:
            ret = requests.get(url, timeout=timeout)
            ret.raise_for_status()
            # 尝试解析为JSON
            try:
                return json.loads(ret.text)
            except json.JSONDecodeError:
                # 如果不是JSON，返回文本
                return ret.text
        except requests.RequestException:
            return None

    @staticmethod
    def _parse_ip_info_source_0(json_data: dict) -> dict:
        """解析source 0的数据"""
        return {
            "ip": json_data.get("ip", ""),
            "country": json_data.get("country", ""),
            "province": json_data.get("pro", ""),
            "city": json_data.get("city", ""),
            "isp": json_data.get("company", ""),
            "cityCode": json_data.get("cityCode", ""),
            "type": json_data.get("type", ""),
        }

    @staticmethod
    def _parse_ip_info_source_1(json_data: dict) -> dict:
        """解析source 1的数据"""
        return {
            "ip": json_data.get("ipinfo", {}).get("text", ""),
            "country": json_data.get("country", ""),
            "province": json_data.get("ipdata", {}).get("info1", ""),
            "city": json_data.get("ipdata", {}).get("info2", ""),
            "district": json_data.get("ipdata", {}).get("info3", ""),
            "isp": json_data.get("ipdata", {}).get("isp", ""),
            "cityCode": json_data.get("adcode", {}).get("a", ""),
            "type": json_data.get("ipinfo", {}).get("type", ""),
        }

    @staticmethod
    def _parse_ip_info_source_2(json_data: dict) -> dict:
        """解析source 2的数据"""
        return {
            "ip": json_data.get("query", ""),
            "country": json_data.get("country", ""),
            "province": json_data.get("regionName", ""),
            "city": json_data.get("city", ""),
            "district": json_data.get("district", ""),
            "isp": json_data.get("isp", ""),
            "cityCode": json_data.get("cityCode", ""),
            "type": json_data.get("type", ""),
            "lat": json_data.get("lat", ""),
            "lon": json_data.get("lon", ""),
        }

    @staticmethod
    def _parse_ip_info_source_7(json_data: dict) -> dict:
        """解析source 7的数据"""
        location = json_data.get("data", {}).get("location", [])
        return {
            "ip": json_data.get("data", {}).get("ip", ""),
            "country": location[0] if len(location) > 0 else "",
            "province": location[1] if len(location) > 1 else "",
            "city": location[2] if len(location) > 2 else "",
            "district": location[3] if len(location) > 3 else "",
            "isp": location[4] if len(location) > 4 else "",
        }

    @staticmethod
    def _parse_ip_info_source_8(json_data: dict) -> dict:
        """解析source 8的数据"""
        return {
            "ip": json_data.get("ip", ""),
            "country": json_data.get("country_name", ""),
            "province": json_data.get("region_name", ""),
            "city": json_data.get("city", ""),
            "district": json_data.get("district", ""),
            "isp": json_data.get("isp", ""),
            "cityCode": json_data.get("city_code", ""),
            "type": json_data.get("type", ""),
            "lat": json_data.get("latitude", ""),
            "lon": json_data.get("longitude", ""),
        }

    @staticmethod
    def _parse_ip_info_source_9(json_data: dict) -> dict:
        """解析source 9的数据"""
        result = json_data.get("result", {})
        return {
            "ip": result.get("ip", ""),
            "country": result.get("country", ""),
            "province": result.get("province", ""),
            "city": result.get("city", ""),
            "district": result.get("district", ""),
            "isp": result.get("operator", ""),
            "cityCode": result.get("administrativeCode", ""),
            "type": result.get("network", ""),
            "lat": result.get("areaLat", ""),
            "lon": result.get("areaLng", ""),
        }

    @staticmethod
    def _parse_ip_info_source_10(json_data: dict) -> dict:
        """解析source 10的数据"""
        result = json_data.get("result", {})
        return {
            "ip": result.get("ip", ""),
            "country": result.get("country", ""),
            "province": result.get("province", ""),
            "city": result.get("city", ""),
            "district": result.get("county", ""),
            "isp": result.get("isp", ""),
            "cityCode": result.get("cityCode", ""),
            "lat": result.get("latitude", ""),
            "lon": result.get("longitude", ""),
        }

    @staticmethod
    def _parse_ip_info_source_11(text_data: str) -> dict:
        """解析source 11的数据（文本格式）"""
        try:
            return {
                "ip": text_data.split("ip = '")[1].split("';")[0],
                "province": text_data.split("ip_province = '")[1].split("';")[0],
                "city": text_data.split("ip_city = '")[1].split("';")[0],
                "isp": text_data.split("ip_isp = '")[1].split("';")[0],
            }
        except (IndexError, ValueError):
            return {}

    @staticmethod
    def _parse_ip_info_source_14(text_data: str) -> dict:
        """解析source 14的数据（文本格式）"""
        try:
            return {
                "ip": text_data.split("IP:")[1].strip(),
            }
        except (IndexError, ValueError):
            return {}

    @staticmethod
    def get_public_ip(ip="", source=10):
        """
        获取公网IP信息
        
        Args:
            ip: IP地址
            source: 获取IP信息的源，默认为10 (0-15)
            
        Returns:
            dict: IP信息字典，失败返回None
        """
        # IP源配置字典：URL模板和处理函数
        ip_sources = {
            0: {
                "url": f"https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true",
                "parser": MeUtils._parse_ip_info_source_0,
                "is_json": True,
            },
            1: {
                "url": f"https://api.vore.top/api/IPdata?ip={ip}",
                "parser": MeUtils._parse_ip_info_source_1,
                "is_json": True,
            },
            2: {
                "url": "http://demo.ip-api.com/json/?lang=zh-CN",
                "parser": MeUtils._parse_ip_info_source_2,
                "is_json": True,
            },
            3: {
                "url": "http://httpbin.org/ip",
                "parser": lambda d: {"ip": d.get("origin", "")},
                "is_json": True,
            },
            4: {
                "url": "https://vv.video.qq.com/checktime?otype=ojson",
                "parser": lambda d: {"ip": d.get("ip", "")},
                "is_json": True,
            },
            5: {
                "url": "https://ipv4.my.ipinfo.app/api/ipDetails.php",
                "parser": lambda d: {"ip": d.get("ip", ""), "country": d.get("country", "")},
                "is_json": True,
            },
            6: {
                "url": "https://r.inews.qq.com/api/ip2city",
                "parser": lambda d: {
                    "ip": d.get("ip", ""),
                    "country": d.get("country", ""),
                    "province": d.get("province", ""),
                    "city": d.get("city", ""),
                    "district": d.get("district", ""),
                    "isp": d.get("isp", ""),
                    "cityCode": d.get("districtCode", ""),
                },
                "is_json": True,
            },
            7: {
                "url": "https://myip.ipip.net/json",
                "parser": MeUtils._parse_ip_info_source_7,
                "is_json": True,
            },
            8: {
                "url": "https://iplark.com/ipstack",
                "parser": MeUtils._parse_ip_info_source_8,
                "is_json": True,
            },
            9: {
                "url": "https://ipservice.ws.126.net/locate/api/getLocByIp",
                "parser": MeUtils._parse_ip_info_source_9,
                "is_json": True,
            },
            10: {
                "url": "https://126.com/fgw/mailsrv-ipdetail/detail",
                "parser": MeUtils._parse_ip_info_source_10,
                "is_json": True,
            },
            11: {
                "url": "http://only-162333-112-96-112-201.nstool.zhuanzfx.com/info.js",
                "parser": MeUtils._parse_ip_info_source_11,
                "is_json": False,
            },
            12: {
                "url": "https://ipv4.gdt.qq.com/get_client_ip",
                "parser": lambda t: {"ip": t.strip()},
                "is_json": False,
            },
            13: {
                "url": "http://fn.syyx.com/my_ip",
                "parser": lambda t: {"ip": t.strip()},
                "is_json": False,
            },
            14: {
                "url": "https://www.uc.cn/ip",
                "parser": MeUtils._parse_ip_info_source_14,
                "is_json": False,
            },
            15: {
                "url": "https://who.nie.163.com/",
                "parser": lambda d: {"ip": d.get("ip", ""), "country": d.get("country", "")},
                "is_json": True,
            },
        }

        # 检查source是否有效
        if source not in ip_sources:
            return None

        try:
            config = ip_sources[source]
            data = MeUtils._fetch_ip_data(config["url"])

            if data is None:
                return None

            # 根据数据类型调用相应的解析器
            if config["is_json"]:
                if isinstance(data, dict):
                    # 类型转换：JSON解析器接收dict
                    parser = cast(Callable[[dict], dict], config["parser"])
                    return parser(data)
                else:
                    # 如果期望JSON但返回了文本，尝试解析
                    try:
                        json_data = json.loads(data)
                        parser = cast(Callable[[dict], dict], config["parser"])
                        return parser(json_data)
                    except (json.JSONDecodeError, TypeError):
                        return None
            else:
                # 文本数据
                if isinstance(data, str):
                    # 类型转换：文本解析器接收str
                    parser = cast(Callable[[str], dict], config["parser"])
                    return parser(data)
                else:
                    return None

        except (KeyError, IndexError, ValueError, TypeError) as e:
            return None

    @staticmethod
    def url_get_domain(url):
        """
        获取URL的域名

        Args:
            url (str): URL字符串

        Returns:
            str: 域名
        """
        parsed_url = urlparse(url)
        return parsed_url.netloc

    @staticmethod
    def get_jsonp(text):
        """
        解析JSONP字符串并返回JSON对象

        Args:
            text (str): JSONP字符串

        Returns:
            dict: 解析后的JSON对象
        """
        jsonp_str = re.search(r"\((.*)\)", text, re.S).group(1)
        return json.loads(jsonp_str)

    @staticmethod
    def save_log(filename, log_content):
        """
        保存日志到指定文件

        :param filename: 日志文件名
        :param log_content: 需要保存的日志内容
        """
        # 定义日志文件夹路径
        log_dir = "logs"
        # 检查log文件夹是否存在，不存在则创建
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 构建完整的文件路径
        file_path = os.path.join(log_dir, filename)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 以追加模式打开文件，如果文件不存在会自动创建
        with open(file_path + ".txt", 'a', encoding='utf-8') as file:
            file.write(f"[{current_time}] {log_content}\n")

    @staticmethod
    def cookie_string_to_dict(cookie_string: str) -> Dict[str, str]:
        """
        将 cookie 字符串转换为字典
        例如: "k1=v1; k2=v2" -> {"k1": "v1", "k2": "v2"}
        """
        cookie_dict: Dict[str, str] = {}
        if not cookie_string:
            return cookie_dict

        for item in cookie_string.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookie_dict[key.strip()] = value.strip()
        return cookie_dict
    @staticmethod
    def _normalize_cookie_input(
            cookie_input: Union[Dict[str, Any], str, Any, None],
            drop_empty: bool = True,
    ) -> Dict[str, str]:
        """
        内部工具：把各种格式的 cookie 统一归一化为 dict[str, str]

        支持:
          - dict: 普通字典
          - 字符串: "k=v; k2=v2"
          - requests.cookies.RequestsCookieJar: requests 库的 CookieJar
          - httpx.Cookies: httpx 库的 Cookies（不直接 import httpx，用特征判断）
          - http.cookies.SimpleCookie: Python 标准库的 SimpleCookie
        同名 key 保留最后一个。
        drop_empty=True 时会丢弃 value 为空/None/空白 的项。

        Args:
            cookie_input: 各种格式的 cookie 输入
            drop_empty: 是否删除空值 cookie

        Returns:
            dict[str, str]: 归一化后的 cookie 字典
        """
        result: Dict[str, str] = {}

        if cookie_input is None:
            return result

        # 1. 字符串
        if isinstance(cookie_input, str):
            tmp = MeUtils.cookie_string_to_dict(cookie_input)
            for k, v in tmp.items():
                result[k] = str(v) if v is not None else ""
            # 统一到后面的 drop_empty 逻辑里去处理
            return {k: v for k, v in result.items()
                    if (not drop_empty) or (str(v).strip() != "")}

        # 2. 字典
        if isinstance(cookie_input, dict):
            for k, v in cookie_input.items():
                result[str(k)] = "" if v is None else str(v)
            return {k: v for k, v in result.items()
                    if (not drop_empty) or (str(v).strip() != "")}

        # 3. http.cookies.SimpleCookie 特殊处理
        cookie_type_name = type(cookie_input).__name__
        if cookie_type_name == "SimpleCookie":
            # SimpleCookie 的每个值是一个 Morsel 对象，需要通过 .value 获取实际值
            try:
                for key, morsel in cookie_input.items():
                    # morsel 可能是 Morsel 对象，需要通过 .value 获取值
                    if hasattr(morsel, 'value'):
                        value = morsel.value
                    else:
                        value = str(morsel)
                    result[str(key)] = "" if value is None else str(value)
                return {k: v for k, v in result.items()
                        if (not drop_empty) or (str(v).strip() != "")}
            except (AttributeError, TypeError, ValueError):
                pass

        # 4. httpx.Cookies 特殊处理（不导入 httpx，用特征判断）
        if cookie_type_name == "Cookies" and hasattr(cookie_input, "jar"):
            # httpx.Cookies: 遍历 jar，同名自动覆盖，保留最后一个
            try:
                for c in cookie_input.jar:
                    result[str(c.name)] = "" if c.value is None else str(c.value)
                return {k: v for k, v in result.items()
                        if (not drop_empty) or (str(v).strip() != "")}
            except (AttributeError, TypeError, ValueError):
                pass

        # 5. requests.cookies.RequestsCookieJar 和其他 CookieJar 类型
        # RequestsCookieJar 支持 dict() 转换和 items() 方法
        try:
            # 先尝试 dict() 转换（RequestsCookieJar 支持）
            tmp = dict(cookie_input)
            for k, v in tmp.items():
                result[str(k)] = "" if v is None else str(v)
            return {k: v for k, v in result.items()
                    if (not drop_empty) or (str(v).strip() != "")}
        except (TypeError, ValueError, AttributeError):
            pass

        # 6. 尝试 items() 方法（很多 CookieJar 类型都支持）
        try:
            if hasattr(cookie_input, "items"):
                tmp_items = list(cookie_input.items())
                for k, v in tmp_items:
                    # 处理 Morsel 对象（SimpleCookie 的 items() 返回 Morsel）
                    if hasattr(v, 'value'):
                        value = v.value
                    else:
                        value = v
                    result[str(k)] = "" if value is None else str(value)
                return {k: v for k, v in result.items()
                        if (not drop_empty) or (str(v).strip() != "")}
        except (TypeError, AttributeError, ValueError):
            pass

        # 7. 尝试迭代（某些 CookieJar 支持直接迭代）
        try:
            if hasattr(cookie_input, '__iter__') and not isinstance(cookie_input, (str, bytes)):
                for item in cookie_input:
                    # 可能是 (key, value) 元组或 Cookie 对象
                    if isinstance(item, tuple) and len(item) >= 2:
                        k, v = item[0], item[1]
                        if hasattr(v, 'value'):
                            value = v.value
                        else:
                            value = v
                        result[str(k)] = "" if value is None else str(value)
                    elif hasattr(item, 'name') and hasattr(item, 'value'):
                        # Cookie 对象
                        result[str(item.name)] = "" if item.value is None else str(item.value)
                if result:
                    return {k: v for k, v in result.items()
                            if (not drop_empty) or (str(v).strip() != "")}
        except (TypeError, AttributeError, ValueError):
            pass

        # 8. 最后兜底：转成字符串再解析一次
        try:
            s = str(cookie_input)
            if s and s != "None":
                tmp = MeUtils.cookie_string_to_dict(s)
                for k, v in tmp.items():
                    result[k] = "" if v is None else str(v)
                return {k: v for k, v in result.items()
                        if (not drop_empty) or (str(v).strip() != "")}
        except Exception:
            pass

        return {}

    @staticmethod
    def cookies_to_string(
            cookie_input: Union[Dict[str, Any], str, Any, None],
            drop_empty: bool = True,
            sep: str = "; "
    ) -> str:
        """
        将 cookie 转成字符串: "key=value; key2=value2" 形式。

        支持以下输入格式：
        - dict: {"key1": "value1", "key2": "value2"}
        - str: "key1=value1; key2=value2"
        - requests.cookies.RequestsCookieJar: requests 库的 CookieJar 对象
        - httpx.Cookies: httpx 库的 Cookies 对象
        - http.cookies.SimpleCookie: Python 标准库的 SimpleCookie 对象
        - None: 返回空字符串

        如果有重名 cookie，内部会去重，保留最后一个。

        Args:
            cookie_input: 各种格式的 cookie 输入
            drop_empty: 是否删除 value 为空/None/空白 的 cookie，默认 True
            sep: 键值对之间的分隔符，默认 "; "

        Returns:
            str: 字符串格式的 cookie，例如 "key1=value1; key2=value2"

        Examples:
            >>> MeUtils.cookies_to_string({"key1": "value1", "key2": "value2"})
            'key1=value1; key2=value2'
            >>> MeUtils.cookies_to_string(None)
            ''
            >>> MeUtils.cookies_to_string("key1=value1; key2=value2")
            'key1=value1; key2=value2'
        """
        data = MeUtils._normalize_cookie_input(cookie_input, drop_empty=drop_empty)
        if not data:
            return ""
        return sep.join(f"{k}={v}" for k, v in data.items())

    @staticmethod
    def cookies_to_dict(
            cookie_input: Union[Dict[str, Any], str, Any, None],
            drop_empty: bool = True,
    ) -> Dict[str, str]:
        """
        将 cookie 统一转为 dict[str, str]，同名 key 保留最后一个。

        支持以下输入格式：
        - dict: {"key1": "value1", "key2": "value2"}
        - str: "key1=value1; key2=value2"
        - requests.cookies.RequestsCookieJar: requests 库的 CookieJar 对象
        - httpx.Cookies: httpx 库的 Cookies 对象
        - http.cookies.SimpleCookie: Python 标准库的 SimpleCookie 对象
        - None: 返回空字典

        如果有重名 cookie，内部会去重，保留最后一个。

        Args:
            cookie_input: 各种格式的 cookie 输入
            drop_empty: 是否删除 value 为空/None/空白 的 cookie，默认 True

        Returns:
            dict[str, str]: Cookie 字典

        Examples:
            >>> MeUtils.cookies_to_dict({"key1": "value1", "key2": "value2"})
            {'key1': 'value1', 'key2': 'value2'}
            >>> MeUtils.cookies_to_dict(None)
            {}
            >>> MeUtils.cookies_to_dict("key1=value1; key2=value2")
            {'key1': 'value1', 'key2': 'value2'}
        """
        return MeUtils._normalize_cookie_input(cookie_input, drop_empty=drop_empty)

    @staticmethod
    def merge_cookies(
            old_cookies: Union[Dict[str, Any], str, Any, None],
            new_cookies: Union[Dict[str, Any], str, Any, None],
            drop_empty: bool = True,
    ) -> Dict[str, str]:
        """
        合并两个 cookie：
        - old_cookies: 旧 cookie
        - new_cookies: 新 cookie
        - 同名 key 时，保留新 cookie 的值（新覆盖旧）
        - drop_empty=True 时，会删除 value 为空/None/空白 的 cookie

        支持以下输入格式（两个参数都支持）：
        - dict: {"key1": "value1", "key2": "value2"}
        - str: "key1=value1; key2=value2"
        - requests.cookies.RequestsCookieJar: requests 库的 CookieJar 对象
        - httpx.Cookies: httpx 库的 Cookies 对象
        - http.cookies.SimpleCookie: Python 标准库的 SimpleCookie 对象
        - None: 视为空 cookie

        如果有重名 cookie，内部会去重，保留最后一个。

        Args:
            old_cookies: 旧 cookie，支持多种类型
            new_cookies: 新 cookie，支持多种类型
            drop_empty: 是否删除空值 cookie，默认 True

        Returns:
            dict[str, str]: 合并后的 cookie 字典

        Examples:
            >>> MeUtils.merge_cookies({"a": "1", "b": "2"}, {"b": "3", "c": "4"})
            {'a': '1', 'b': '3', 'c': '4'}
            >>> MeUtils.merge_cookies("a=1; b=2", "b=3; c=4")
            {'a': '1', 'b': '3', 'c': '4'}
        """
        old_dict = MeUtils._normalize_cookie_input(old_cookies, drop_empty=False)
        new_dict = MeUtils._normalize_cookie_input(new_cookies, drop_empty=False)

        # 先旧后新，新覆盖旧
        merged: Dict[str, str] = {}
        merged.update(old_dict)
        merged.update(new_dict)

        # 最后统一做一次 drop_empty
        if drop_empty:
            merged = {k: v for k, v in merged.items() if str(v).strip() != ""}

        return merged





