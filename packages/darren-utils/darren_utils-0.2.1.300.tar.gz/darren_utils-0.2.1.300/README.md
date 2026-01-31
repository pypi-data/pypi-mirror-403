# darren_utils

一个功能丰富的Python工具库，提供加密解密、哈希计算、HTTP请求、字符串处理、时间处理、文件操作、系统信息和硬件信息获取等多种实用功能。

## ✨ 特性

- 🔐 **多种加密算法**：支持AES、DES、3DES、RSA、RC4、SM2、SM4等国密算法
- 🔑 **哈希算法**：MD5、SHA系列、SM3、HMAC等
- 🌐 **网络工具**：HTTP请求、IP查询、URL处理等
- 📁 **文件操作**：文件读写、复制、删除、枚举等
- ⏰ **时间处理**：时间戳、格式化、随机时间戳等
- 🔤 **字符串处理**：随机字符串、字符串提取、URL编解码等
- 💻 **系统工具**：硬件信息、系统版本、进程管理、端口检测等
- 📋 **剪贴板操作**：读写剪贴板内容
- ⚙️ **配置管理**：配置文件读写

## 📦 安装

```bash
pip install darren_utils
```

## 🚀 快速开始

```python
import darren

# 时间工具
timestamp = darren.time.get_timestamp()
print(f"当前时间戳: {timestamp}")

# 字符串工具
random_str = darren.string.random_string(10)
print(f"随机字符串: {random_str}")

# 文件工具
if darren.file.file_exists("test.txt"):
    print("文件存在")

# 哈希工具
md5_hash = darren.hash.hash_md5_string("hello world")
print(f"MD5: {md5_hash}")

# 加密工具
encrypted = darren.aes.encrypt_string("mykey", "hello world")
decrypted = darren.aes.decrypt_string("mykey", encrypted)
print(f"解密结果: {decrypted}")

# 系统工具
cpu_info = darren.sys.system_get_cpu_info()
print(f"CPU信息: {cpu_info}")

# 工具函数
ip_info = darren.utils.get_public_ip()
print(f"公网IP: {ip_info}")
```

## 📚 API 文档

### 时间工具 (darren.time)

| 方法                   | 描述      | 参数                                                                      | 返回值                 |
| -------------------- | ------- | ----------------------------------------------------------------------- | ------------------- |
| `get_timestamp()`    | 获取当前时间戳 | `is_10_digits=False`                                                    | `int`: 时间戳（默认13位毫秒） |
| `random_timestamp()` | 生成随机时间戳 | 无                                                                       | `float`: 随机时间戳      |
| `format()`           | 格式化时间   | `time_value`, `date_format=None`, `time_format=None`, `is_24_hour=True` | `str`: 格式化后的时间字符串   |

**示例：**

```python
# 获取13位毫秒时间戳
timestamp = darren.time.get_timestamp()

# 获取10位秒时间戳
timestamp_10 = darren.time.get_timestamp(is_10_digits=True)

# 格式化时间
formatted = darren.time.format(
    timestamp, 
    date_format="yyyy/M/d dddd",
    time_format="hh:mm:ss"
)
```

### 字符串工具 (darren.string)

| 方法                | 描述          | 参数                                                       | 返回值          |
| ----------------- | ----------- | -------------------------------------------------------- | ------------ |
| `random_string()` | 生成随机字符串     | `num`, `uppercase=True`, `lowercase=True`, `digits=True` | `str`: 随机字符串 |
| `get_between()`   | 获取两个文本之间的内容 | `text`, `start_text`, `end_text`                         | `str`: 中间内容  |
| `get_left()`      | 获取分隔符左边的内容  | `text`, `delimiter`                                      | `str`: 左边内容  |
| `get_right()`     | 获取分隔符右边的内容  | `text`, `delimiter`                                      | `str`: 右边内容  |

**示例：**

```python
# 生成随机字符串
random_str = darren.string.random_string(10, uppercase=True, lowercase=True, digits=True)

# 提取文本
text = "start中间内容end"
result = darren.string.get_between(text, "start", "end")  # "中间内容"
```

### 文件工具 (darren.file)

| 方法                 | 描述       | 参数                                                                                     | 返回值                  |
| ------------------ | -------- | -------------------------------------------------------------------------------------- | -------------------- |
| `file_exists()`    | 检查文件是否存在 | `file_path`                                                                            | `bool`: 是否存在         |
| `dir_exists()`     | 检查目录是否存在 | `dir_path`                                                                             | `bool`: 是否存在         |
| `file_read()`      | 读取文件内容   | `path`                                                                                 | `str`: 文件内容          |
| `file_copy()`      | 复制文件     | `src_path`, `dest_path`, `overwrite=False`                                             | `bool/int`: 成功返回True |
| `file_delete()`    | 删除文件     | `file_path`, `to_trash=True`                                                           | `bool/int`: 成功返回True |
| `file_enumerate()` | 枚举目录文件   | `directory`, `pattern="*.*"`, `with_path=False`, `sort_alpha=False`, `recursive=False` | `list`: 文件列表         |
| `file_size()`      | 获取文件大小   | `file_path`, `unit="M"`                                                                | `str`: 格式化大小         |
| `file_get_info()`  | 获取文件信息   | `file_path`                                                                            | `dict`: 文件信息字典       |

**示例：**

```python
# 检查文件是否存在
if darren.file.file_exists("test.txt"):
    print("文件存在")

# 枚举Python文件
py_files = darren.file.file_enumerate(".", "*.py", recursive=True)
print(f"找到 {len(py_files)} 个Python文件")

# 获取文件信息
info = darren.file.file_get_info("test.txt")
print(f"文件大小: {info['size_formatted']}")
```

### 哈希工具 (darren.hash / darren.hash_utils)

| 方法                     | 描述        | 参数     | 返回值            |
| ---------------------- | --------- | ------ | -------------- |
| `hash_md5_string()`    | MD5哈希     | `text` | `str`: MD5值    |
| `hash_sha1_string()`   | SHA1哈希    | `text` | `str`: SHA1值   |
| `hash_sha256_string()` | SHA256哈希  | `text` | `str`: SHA256值 |
| `hash_sha512_string()` | SHA512哈希  | `text` | `str`: SHA512值 |
| `hash_sm3_string()`    | SM3哈希（国密） | `text` | `str`: SM3值    |

**示例：**

```python
# MD5哈希
md5 = darren.hash.hash_md5_string("hello world")

# SHA256哈希
sha256 = darren.hash.hash_sha256_string("hello world")
```

### HMAC工具 (darren.hmac)

| 方法              | 描述          | 参数               | 返回值          |
| --------------- | ----------- | ---------------- | ------------ |
| `hmac_md5()`    | HMAC-MD5    | `key`, `message` | `str`: HMAC值 |
| `hmac_sha256()` | HMAC-SHA256 | `key`, `message` | `str`: HMAC值 |
| `hmac_sha512()` | HMAC-SHA512 | `key`, `message` | `str`: HMAC值 |

**示例：**

```python
hmac_value = darren.hmac.hmac_sha256("secret_key", "message")
```

### AES加密 (darren.aes)

| 方法                 | 描述    | 参数                  | 返回值            |
| ------------------ | ----- | ------------------- | -------------- |
| `encrypt_string()` | AES加密 | `key`, `plaintext`  | `str`: 加密后的字符串 |
| `decrypt_string()` | AES解密 | `key`, `ciphertext` | `str`: 解密后的字符串 |

**示例：**

```python
# 加密
encrypted = darren.aes.encrypt_string("my_secret_key", "hello world")

# 解密
decrypted = darren.aes.decrypt_string("my_secret_key", encrypted)
```

### RSA加密 (darren.rsa)

| 方法                   | 描述       | 参数                                                        | 返回值               |
| -------------------- | -------- | --------------------------------------------------------- | ----------------- |
| `generate_keypair()` | 生成RSA密钥对 | `key_size=2048`                                           | `tuple`: (私钥, 公钥) |
| `encrypt()`          | RSA加密    | `plaintext`, `public_key`, `padding_scheme='OAEP'`        | `str`: Base64编码密文 |
| `decrypt()`          | RSA解密    | `ciphertext`, `private_key`, `padding_scheme='OAEP'`      | `str`: 明文         |
| `sign()`             | RSA签名    | `data`, `private_key`, `padding_scheme='PSS'`             | `str`: Base64编码签名 |
| `verify()`           | RSA验证签名  | `data`, `signature`, `public_key`, `padding_scheme='PSS'` | `bool`: 验证结果      |

**示例：**

```python
# 生成密钥对
private_key, public_key = darren.rsa.generate_keypair()

# 加密
encrypted = darren.rsa.encrypt("hello", public_key)

# 解密
decrypted = darren.rsa.decrypt(encrypted, private_key)

# 签名
signature = darren.rsa.sign("data", private_key)

# 验证
is_valid = darren.rsa.verify("data", signature, public_key)
```

### 国密算法

#### SM2加密 (darren.sm2)

```python
# 生成密钥对
private_key, public_key = darren.sm2.generate_keypair()

# 加密
encrypted = darren.sm2.encrypt_string(public_key, "hello")

# 解密
decrypted = darren.sm2.decrypt_string(private_key, encrypted)
```

#### SM3哈希 (darren.sm3)

```python
hash_value = darren.sm3.hash_sm3_string("hello world")
```

#### SM4加密 (darren.sm4)

```python
encrypted = darren.sm4.encrypt_string("key", "hello")
decrypted = darren.sm4.decrypt_string("key", encrypted)
```

### 系统工具 (darren.sys)

| 方法                       | 描述        | 参数                       | 返回值               |
| ------------------------ | --------- | ------------------------ | ----------------- |
| `system_get_cpu_info()`  | 获取CPU信息   | 无                        | `dict`: CPU信息字典   |
| `system_get_version()`   | 获取系统版本信息  | 无                        | `dict`: 系统信息字典    |
| `get_devices_md5()`      | 获取设备指纹MD5 | `uppercase=False`        | `str`: MD5值       |
| `port_check_process()`   | 检查端口占用    | `port`, `protocol='tcp'` | `dict/None`: 进程信息 |
| `process_kill_by_pid()`  | 根据PID结束进程 | `pid`, `force=False`     | `bool`: 是否成功      |
| `process_kill_by_name()` | 根据进程名结束进程 | `name`, `force=False`    | `int`: 结束的进程数     |

**示例：**

```python
# 获取CPU信息
cpu_info = darren.sys.system_get_cpu_info()
print(f"CPU型号: {cpu_info['model']}")
print(f"核心数: {cpu_info['cores']}")

# 获取设备指纹
device_id = darren.sys.get_devices_md5()

# 检查端口占用
process = darren.sys.port_check_process(8080)
if process:
    print(f"端口被进程占用: {process['name']}")
```

### 工具函数 (darren.utils)

| 方法                    | 描述         | 参数                                              | 返回值                 |
| --------------------- | ---------- | ----------------------------------------------- | ------------------- |
| `is_empty()`          | 判断值是否为空    | `value`                                         | `bool`: 是否为空        |
| `is_not_empty()`      | 判断值是否不为空   | `value`                                         | `bool`: 是否不为空       |
| `get_public_ip()`     | 获取公网IP信息   | `ip=""`, `source=10`                            | `dict/None`: IP信息   |
| `url_encode()`        | URL编码      | `text`, `is_utf8=True`                          | `str`: 编码后的字符串      |
| `url_decode()`        | URL解码      | `encoded_text`, `is_utf8=True`                  | `str`: 解码后的字符串      |
| `url_get_param()`     | 获取URL参数    | `url`, `param_name`                             | `str`: 参数值          |
| `json_parse_safe()`   | 安全JSON解析   | `obj`                                           | `dict/list`: JSON对象 |
| `json_get_nested()`   | 获取嵌套JSON值  | `obj`, `path`, `default=""`                     | 任意: 获取的值            |
| `cookies_to_string()` | Cookie转字符串 | `cookie_input`, `drop_empty=True`, `sep="; "`   | `str`: Cookie字符串    |
| `cookies_to_dict()`   | Cookie转字典  | `cookie_input`, `drop_empty=True`               | `dict`: Cookie字典    |
| `merge_cookies()`     | 合并Cookie   | `old_cookies`, `new_cookies`, `drop_empty=True` | `dict`: 合并后的Cookie  |

**示例：**

```python
# 判断是否为空
if darren.utils.is_empty(""):
    print("值为空")

# 获取公网IP
ip_info = darren.utils.get_public_ip()
print(f"IP: {ip_info.get('ip')}")

# URL编码
encoded = darren.utils.url_encode("hello world")
decoded = darren.utils.url_decode(encoded)

# JSON嵌套获取
data = {"user": {"name": "Darren", "age": 30}}
name = darren.utils.json_get_nested(data, "user.name")  # "Darren"
```

### 剪贴板工具 (darren.cli)

| 方法        | 描述      | 参数     | 返回值          |
| --------- | ------- | ------ | ------------ |
| `read()`  | 读取剪贴板内容 | 无      | `str`: 剪贴板内容 |
| `write()` | 写入剪贴板内容 | `text` | `bool`: 是否成功 |

**示例：**

```python
# 读取剪贴板
content = darren.cli.read()

# 写入剪贴板
darren.cli.write("Hello, Clipboard!")
```

### 配置工具 (darren.config)

| 方法                   | 描述    | 参数                                                 | 返回值                   |
| -------------------- | ----- | -------------------------------------------------- | --------------------- |
| `initConfig()`       | 初始化配置 | `config_file_path`                                 | `ConfigParser`: 配置解析器 |
| `get_config_value()` | 获取配置值 | `config_parser`, `section`, `option`, `default=''` | `str`: 配置值            |

**示例：**

```python
# 初始化配置
config = darren.config.initConfig("config.ini")

# 获取配置值
value = darren.config.get_config_value(config, "section", "key", "default")
```

## 🔧 其他加密算法

### DES加密 (darren.des)

```python
encrypted = darren.des.encrypt_string("key", "hello")
decrypted = darren.des.decrypt_string("key", encrypted)
```

### 3DES加密 (darren.tdes)

```python
encrypted = darren.tdes.encrypt_string("key", "hello")
decrypted = darren.tdes.decrypt_string("key", encrypted)
```

### RC4加密 (darren.rc4)

```python
encrypted = darren.rc4.encrypt_string("key", "hello")
decrypted = darren.rc4.decrypt_string("key", encrypted)
```

## 📋 完整示例

```python
import darren

# 1. 时间处理
timestamp = darren.time.get_timestamp()
formatted_time = darren.time.format(timestamp, date_format="yyyy/M/d", time_format="hh:mm:ss")
print(f"当前时间: {formatted_time}")

# 2. 字符串处理
random_str = darren.string.random_string(10)
text = "start中间内容end"
between = darren.string.get_between(text, "start", "end")

# 3. 文件操作
if darren.file.file_exists("test.txt"):
    files = darren.file.file_enumerate(".", "*.py", recursive=True)
    file_info = darren.file.file_get_info("test.txt")

# 4. 哈希计算
md5 = darren.hash.hash_md5_string("hello")
sha256 = darren.hash.hash_sha256_string("hello")

# 5. 加密解密
# AES
encrypted = darren.aes.encrypt_string("key", "secret")
decrypted = darren.aes.decrypt_string("key", encrypted)

# RSA
private_key, public_key = darren.rsa.generate_keypair()
encrypted = darren.rsa.encrypt("secret", public_key)
decrypted = darren.rsa.decrypt(encrypted, private_key)

# 6. 系统信息
cpu_info = darren.sys.system_get_cpu_info()
system_info = darren.sys.system_get_version()
device_id = darren.sys.get_devices_md5()

# 7. 网络工具
ip_info = darren.utils.get_public_ip(source=10)
encoded_url = darren.utils.url_encode("hello world")

# 8. Cookie处理
cookie_dict = {"name": "value", "token": "abc123"}
cookie_str = darren.utils.cookies_to_string(cookie_dict)
cookie_dict2 = darren.utils.cookies_to_dict(cookie_str)

# 9. 剪贴板
darren.cli.write("Hello!")
content = darren.cli.read()
```

## 🛠️ 开发

### 项目结构

```
darren_utils/
├── darren.py              # 主入口模块
├── TimeUtils.py           # 时间工具
├── StringUtils.py         # 字符串工具
├── FileUtils.py           # 文件工具
├── SystemUtils.py         # 系统工具
├── MeUtils.py             # 通用工具
├── config_utils.py        # 配置工具
├── darren_clipboard.py    # 剪贴板工具
├── encry/                 # 加密模块
│   ├── darren_aes.py
│   ├── darren_rsa.py
│   ├── darren_sm2.py
│   ├── HashUtils.py
│   └── ...
└── proxy/                 # 代理模块
```

## 📝 更新日志

### v0.2.1.209

- ✨ 重构 `get_public_ip` 方法，提升代码可维护性
- 🐛 修复 `get_devices_md5` 方法中的bug
- 🐛 修复类型检查错误
- ✨ 添加类型注解，提升IDE支持
- 🧹 清理空文件和调试代码

## 📄 许可证

MIT License

## 👤 作者

Darren - 2775856@qq.com

## 🔗 链接

- GitHub: [https://github.com/Darren5211314](https://github.com/Darren5211314)
- PyPI: [https://pypi.org/project/darren_utils](https://pypi.org/project/darren_utils)

## ⭐ 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如有问题或建议，请通过以下方式联系：

- Email: 2775856@qq.com
- GitHub Issues: [提交Issue](https://github.com/Darren5211314/issues)
