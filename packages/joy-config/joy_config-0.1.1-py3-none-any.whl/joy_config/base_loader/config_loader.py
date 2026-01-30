import os
import configparser

from loguru import logger


def config_loader(config_path="config.ini", section=None):
    """
    加载配置文件中的配置项，并将这些配置项作为返回对象的属性
    
    参数:
        config_path: 配置文件的路径，默认为当前目录下的config.ini文件
        section: 要加载的配置节，如果为None则加载所有节
        
    返回:
        一个包含配置项作为属性的ConfigObject对象
    """
    class ConfigObject:
        """
        存储配置项的配置类
        """
        def __init__(self, config_file, section=None):
            self._config_file = config_file
            self._section = section
            self._config = configparser.ConfigParser()
            self._load_config()
        
        def _load_config(self):
            """加载配置文件"""
            try:
                if not os.path.exists(self._config_file):
                    logger.error(f"can't find the config file '{self._config_file}'")
                    return
                
                self._config.read(self._config_file, encoding='utf-8')
                
                # 如果指定了节，只加载该节
                if self._section:
                    if self._section in self._config:
                        self._load_section(self._section)
                    else:
                        logger.error(f"section '{self._section}' not found in config file")
                else:
                    # 加载所有节
                    for section in self._config.sections():
                        self._load_section(section)
            except Exception as e:
                logger.error(f"can't load the config file: {e}")
        
        def _load_section(self, section):
            """加载指定节的配置项"""
            # 为每个节创建一个属性
            section_obj = type('SectionConfig', (), {})()
            
            for key, value in self._config[section].items():
                # 尝试转换值的类型
                try:
                    # 尝试转换为整数
                    value = int(value)
                except ValueError:
                    try:
                        # 尝试转换为浮点数
                        value = float(value)
                    except ValueError:
                        # 尝试转换为布尔值
                        if value.lower() in ('true', 'yes', '1'):
                            value = True
                        elif value.lower() in ('false', 'no', '0'):
                            value = False
                
                # 设置属性到节对象
                setattr(section_obj, key, value)
            
            # 如果只加载一个节，直接设置属性到主对象
            if self._section:
                for key, value in self._config[section].items():
                    setattr(self, key, getattr(section_obj, key))
            else:
                # 设置节对象为主对象的属性
                setattr(self, section, section_obj)
        
        def get(self, key, default=None):
            """获取配置项值，如果不存在则返回默认值"""
            # 如果包含点，表示访问节下的属性
            if '.' in key:
                section, option = key.split('.', 1)
                section_obj = getattr(self, section, None)
                if section_obj:
                    return getattr(section_obj, option, default)
                return default
            return getattr(self, key, default)
        
        def as_dict(self):
            """将所有配置项转换为字典返回"""
            result = {}
            for key, value in self.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, object) and not isinstance(value, (str, int, float, bool, list, dict)):
                        # 如果是节对象，递归转换
                        section_dict = {}
                        for attr in dir(value):
                            if not attr.startswith('_') and not callable(getattr(value, attr)):
                                section_dict[attr] = getattr(value, attr)
                        result[key] = section_dict
                    else:
                        result[key] = value
            return result
        
        def __repr__(self):
            if self._section:
                attrs = ', '.join(f"{key}={repr(value)}" for key, value in self.__dict__.items() 
                                 if not key.startswith('_'))
                return f"ConfigObject({self._section}: {attrs})"
            else:
                sections = ', '.join(key for key in self.__dict__ if not key.startswith('_'))
                return f"ConfigObject(sections: {sections})"
        
        def __getitem__(self, key):
            """支持字典式访问: config['section.key'] 或 config['section']['key']"""
            if '.' in key:
                section, option = key.split('.', 1)
                section_obj = getattr(self, section, None)
                if section_obj:
                    try:
                        return getattr(section_obj, option)
                    except AttributeError:
                        raise KeyError(option)
                raise KeyError(section)
            try:
                return getattr(self, key)
            except AttributeError:
                raise KeyError(key)
    
    return ConfigObject(config_path, section)
