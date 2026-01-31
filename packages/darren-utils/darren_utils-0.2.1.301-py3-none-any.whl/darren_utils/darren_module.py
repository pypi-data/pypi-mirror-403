"""
Darren 工具包主入口
提供时间、字符串、文件等常用工具方法
"""
from .FileUtils import FileUtils
from .config_utils import ConfigUtils
from .darren_clipboard import Clipboard
from .encry.HashUtils import HashUtils
from .encry.HmacUtils import HmacUtils
from .MeUtils import MeUtils
from .StringUtils import StringUtils
from .SystemUtils import SystemUtils
from .TimeUtils import TimeUtils
from .encry.darren_3des import TdesUtils
from .encry.darren_3des_js import TdesUtilsJS
from .encry.darren_aes import AesUtils
from .encry.darren_des import DesUtils
from .encry.darren_rc4 import Rc4Utils
from .encry.darren_rsa import RsaUtils
from .encry.darren_sm2 import SM2Utils
from .encry.darren_sm3 import SM3Utils
from .encry.darren_sm4 import SM4Utils

# 创建实例作为模块属性
time: TimeUtils = TimeUtils()
string: StringUtils = StringUtils()
file: FileUtils = FileUtils()
utils: MeUtils = MeUtils()
sys: SystemUtils = SystemUtils()
hash_utils: HashUtils = HashUtils()  # 避免覆盖内置函数 hash
hash = hash_utils  # 向后兼容别名
hmac: HmacUtils = HmacUtils()
tdes: TdesUtils = TdesUtils()
tdes_js: TdesUtilsJS = TdesUtilsJS()
aes: AesUtils = AesUtils()
des: DesUtils = DesUtils()
rc4: Rc4Utils = Rc4Utils()
rsa: RsaUtils = RsaUtils()
sm2: SM2Utils = SM2Utils()
sm3: SM3Utils = SM3Utils()
sm4: SM4Utils = SM4Utils()
cli: Clipboard = Clipboard()
config: ConfigUtils = ConfigUtils()


