import configparser


class ConfigUtils:
    @staticmethod
    def initConfig(config_file_path):
        """加载配置文件"""
        config_parser = configparser.ConfigParser()
        config_parser.read(config_file_path, encoding='utf-8')
        return config_parser

    @staticmethod
    def get_config_value(config_parser,section, option, default=''):
        """
        从配置文件获取指定节点下的配置值
        Args:
            config_parser : 加载工具
            section: 配置节点名称 (如 'proxy')
            option: 配置项名称 (如 'api_url')
            default: 默认值

        Returns:
            str: 配置值或默认值
        """
        return config_parser.get(section, option, fallback=default)

