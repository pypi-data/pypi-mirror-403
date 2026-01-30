import os
import sys
import json
import yaml
import configparser
from pathlib import Path

from loguru import logger
from .base_loader.dotenv_loader import dotenv_loader as env_loader
from .base_loader.yaml_loader import yaml_loader
from .base_loader.json_loader import json_loader
from .base_loader.config_loader import config_loader

def auto_loader(config_path=None, env=None):
    """
    根据文件扩展名和环境自动选择合适的加载器来加载配置文件
    
    参数:
        config_path: 配置文件的路径，如果为None，则按优先级尝试加载常见配置文件
        env: 环境名称（如'dev', 'test', 'prod'），如果为None则尝试从环境变量中获取
        
    返回:
        一个包含配置项作为属性的配置对象
    """
    # 确定项目根目录
    root_dir = _get_project_root()
    logger.debug(f"项目根目录: {root_dir}")
    
    # 确定当前环境
    if env is None:
        # 尝试从环境变量获取环境名称
        env = os.environ.get('ENV', os.environ.get('ENVIRONMENT', os.environ.get('PROFILE', 'dev')))
    
    logger.info(f"当前环境: {env}")
    
    # 如果未指定配置文件路径，则按优先级尝试常见配置文件
    if config_path is None:
        # 按优先级定义常见配置文件，包括环境特定的配置文件
        common_config_files = []
        
        # 环境特定的配置文件优先级更高
        if env:
            common_config_files.extend([
                os.path.join(root_dir, f"config-{env}.yaml"), os.path.join(root_dir, f"config-{env}.yml"),
                os.path.join(root_dir, f"config-{env}.json"),
                os.path.join(root_dir, f"config-{env}.ini"), os.path.join(root_dir, f"config-{env}.cfg"),
                os.path.join(root_dir, f"application-{env}.yaml"), os.path.join(root_dir, f"application-{env}.yml"),
                os.path.join(root_dir, f"application-{env}.json"),
                os.path.join(root_dir, f"application-{env}.properties"), os.path.join(root_dir, f"application-{env}.ini"),
                os.path.join(root_dir, f".env.{env}")
            ])
            
            # 也检查配置目录
            config_dir = os.path.join(root_dir, "config")
            if os.path.exists(config_dir) and os.path.isdir(config_dir):
                common_config_files.extend([
                    os.path.join(config_dir, f"config-{env}.yaml"), os.path.join(config_dir, f"config-{env}.yml"),
                    os.path.join(config_dir, f"config-{env}.json"),
                    os.path.join(config_dir, f"config-{env}.ini"), os.path.join(config_dir, f"config-{env}.cfg"),
                    os.path.join(config_dir, f"application-{env}.yaml"), os.path.join(config_dir, f"application-{env}.yml"),
                    os.path.join(config_dir, f"application-{env}.json"),
                    os.path.join(config_dir, f"application-{env}.properties"), os.path.join(config_dir, f"application-{env}.ini"),
                    os.path.join(config_dir, f".env.{env}")
                ])
        
        # 然后是通用配置文件
        common_config_files.extend([
            os.path.join(root_dir, ".env"),
            os.path.join(root_dir, "config.yaml"), os.path.join(root_dir, "config.yml"),
            os.path.join(root_dir, "config.json"),
            os.path.join(root_dir, "config.ini"), os.path.join(root_dir, "config.cfg"),
            os.path.join(root_dir, "application.yaml"), os.path.join(root_dir, "application.yml"),
            os.path.join(root_dir, "application.json"),
            os.path.join(root_dir, "application.properties"), os.path.join(root_dir, "application.ini")
        ])
        
        # 检查配置目录中的通用配置文件
        config_dir = os.path.join(root_dir, "config")
        if os.path.exists(config_dir) and os.path.isdir(config_dir):
            common_config_files.extend([
                os.path.join(config_dir, ".env"),
                os.path.join(config_dir, "config.yaml"), os.path.join(config_dir, "config.yml"),
                os.path.join(config_dir, "config.json"),
                os.path.join(config_dir, "config.ini"), os.path.join(config_dir, "config.cfg"),
                os.path.join(config_dir, "application.yaml"), os.path.join(config_dir, "application.yml"),
                os.path.join(config_dir, "application.json"),
                os.path.join(config_dir, "application.properties"), os.path.join(config_dir, "application.ini")
            ])
        
        # 尝试查找存在的配置文件
        for file_path in common_config_files:
            if os.path.exists(file_path):
                config_path = file_path
                logger.info(f"自动检测到配置文件: {config_path}")
                break
        
        if config_path is None:
            logger.warning("未找到任何配置文件，返回空配置")
            # 返回一个空的配置对象
            return type('EmptyConfig', (), {
                'get': lambda self, key, default=None: default,
                'as_dict': lambda self: {},
                '__repr__': lambda self: "EmptyConfig()",
                '__getitem__': lambda self, key: None
            })()
    else:
        # 如果提供的配置路径是相对路径，则相对于项目根目录
        if not os.path.isabs(config_path):
            config_path = os.path.join(root_dir, config_path)
    
    # 加载基础配置
    base_config = _load_config_file(config_path)
    
    # 如果存在环境特定的配置文件，加载并合并
    if env and config_path:
        # 从基础配置文件路径推断环境特定的配置文件路径
        base_name, ext = os.path.splitext(config_path)
        env_config_path = f"{base_name}-{env}{ext}"
        
        # 如果环境特定的配置文件存在，加载并合并
        if os.path.exists(env_config_path):
            logger.info(f"加载环境特定配置文件: {env_config_path}")
            env_config = _load_config_file(env_config_path)
            
            # 合并配置
            base_config = _merge_configs(base_config, env_config)
    
    return base_config


def _get_project_root():
    """
    尝试确定项目的根目录
    
    返回:
        项目根目录的路径
    """
    # 方法1: 使用当前工作目录
    cwd = os.getcwd()
    
    # 方法2: 如果是在包中运行，尝试查找包的根目录
    try:
        # 获取调用栈中的主模块
        main_module = sys.modules['__main__']
        if hasattr(main_module, '__file__'):
            # 主模块文件所在的目录可能是项目根目录
            main_dir = os.path.dirname(os.path.abspath(main_module.__file__))
            
            # 检查是否有一些典型的项目根目录标志
            if (os.path.exists(os.path.join(main_dir, 'setup.py')) or
                os.path.exists(os.path.join(main_dir, 'pyproject.toml')) or
                os.path.exists(os.path.join(main_dir, '.git'))):
                return main_dir
    except (KeyError, AttributeError):
        pass
    
    # 方法3: 向上查找项目标志文件
    path = Path(cwd)
    for p in [path] + list(path.parents):
        if (p / 'setup.py').exists() or (p / 'pyproject.toml').exists() or (p / '.git').exists():
            return str(p)
    
    # 如果找不到明确的项目根目录，返回当前工作目录
    return cwd


def _load_config_file(config_path):
    """
    根据文件扩展名加载配置文件
    
    参数:
        config_path: 配置文件的路径
        
    返回:
        一个包含配置项的配置对象
    """
    # 根据文件扩展名选择合适的加载器
    _, ext = os.path.splitext(config_path.lower())
    
    if ext == '.env':
        logger.info(f"使用env_loader加载: {config_path}")
        return env_loader(config_path)
    elif ext in ['.yaml', '.yml']:
        logger.info(f"使用yaml_loader加载: {config_path}")
        return yaml_loader(config_path)
    elif ext == '.json':
        logger.info(f"使用json_loader加载: {config_path}")
        return json_loader(config_path)
    elif ext in ['.ini', '.cfg', '.properties']:
        logger.info(f"使用config_loader加载: {config_path}")
        return config_loader(config_path)
    else:
        # 如果无法识别扩展名，尝试根据内容推断文件类型
        logger.info(f"无法识别的文件扩展名: {ext}，尝试根据内容推断文件类型")
        return _load_by_content(config_path)
    
    
def _merge_configs(base_config, env_config):
    """
    合并两个配置对象
    
    参数:
        base_config: 基础配置对象
        env_config: 环境特定配置对象
        
    返回:
        合并后的配置对象
    """
    # 将环境配置转换为字典
    env_dict = env_config.as_dict() if hasattr(env_config, 'as_dict') else {}
    
    # 创建一个新的配置类
    class MergedConfig:
        def __init__(self, base, env_dict):
            self._base = base
            
            # 将环境配置的属性复制到新对象
            for key, value in env_dict.items():
                if isinstance(value, dict):
                    # 如果是嵌套字典，递归合并
                    base_value = getattr(base, key, None)
                    if base_value and hasattr(base_value, 'as_dict'):
                        # 如果基础配置中有相同的嵌套对象，合并它们
                        merged_obj = _merge_nested_dict(base_value, value)
                        setattr(self, key, merged_obj)
                    else:
                        # 否则创建新的嵌套对象
                        nested_obj = type('NestedConfig', (), {})()
                        for k, v in value.items():
                            setattr(nested_obj, k, v)
                        setattr(self, key, nested_obj)
                else:
                    # 直接覆盖基础配置
                    setattr(self, key, value)
        
        def get(self, key, default=None):
            """获取配置项值，如果不存在则返回默认值"""
            # 先尝试从环境配置获取
            try:
                if '.' in key:
                    parts = key.split('.')
                    obj = self
                    for part in parts[:-1]:
                        obj = getattr(obj, part, None)
                        if obj is None:
                            # 如果中间路径不存在，回退到基础配置
                            return self._base.get(key, default)
                    return getattr(obj, parts[-1], None) or self._base.get(key, default)
                else:
                    return getattr(self, key, None) or self._base.get(key, default)
            except (AttributeError, KeyError):
                # 如果环境配置中不存在，回退到基础配置
                return self._base.get(key, default)
        
        def as_dict(self):
            """将所有配置项转换为字典返回"""
            # 先获取基础配置的字典
            result = self._base.as_dict() if hasattr(self._base, 'as_dict') else {}
            
            # 然后添加或覆盖环境配置的项
            for key, value in self.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, object) and not isinstance(value, (str, int, float, bool, list, dict)):
                        # 如果是嵌套对象，递归转换
                        nested_dict = {}
                        for attr in dir(value):
                            if not attr.startswith('_') and not callable(getattr(value, attr)):
                                attr_value = getattr(value, attr)
                                if isinstance(attr_value, object) and not isinstance(attr_value, (str, int, float, bool, list, dict)):
                                    # 递归处理更深层次的嵌套
                                    nested_obj = type('NestedConfig', (), {})()
                                    nested_obj.__dict__.update(attr_value.__dict__)
                                    nested_dict[attr] = nested_obj.as_dict() if hasattr(nested_obj, 'as_dict') else attr_value
                                else:
                                    nested_dict[attr] = attr_value
                        result[key] = nested_dict
                    else:
                        result[key] = value
            
            return result
        
        def __repr__(self):
            attrs = []
            for key, value in self.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, object) and not isinstance(value, (str, int, float, bool, list, dict)):
                        attrs.append(f"{key}=<nested>")
                    else:
                        attrs.append(f"{key}={repr(value)}")
            return f"MergedConfig({', '.join(attrs)})"
        
        def __getitem__(self, key):
            """支持字典式访问: config['key'] 或 config['nested.key']"""
            if '.' in key:
                parts = key.split('.')
                obj = self
                for part in parts[:-1]:
                    try:
                        obj = getattr(obj, part)
                    except AttributeError:
                        # 如果在环境配置中找不到，尝试从基础配置获取
                        try:
                            return self._base[key]
                        except (KeyError, AttributeError):
                            raise KeyError(part)
                try:
                    return getattr(obj, parts[-1])
                except AttributeError:
                    # 如果在环境配置中找不到，尝试从基础配置获取
                    try:
                        return self._base[key]
                    except (KeyError, AttributeError):
                        raise KeyError(parts[-1])
            
            try:
                return getattr(self, key)
            except AttributeError:
                # 如果在环境配置中找不到，尝试从基础配置获取
                try:
                    return self._base[key]
                except (KeyError, AttributeError):
                    raise KeyError(key)
    
    return MergedConfig(base_config, env_dict)


def _merge_nested_dict(base_obj, env_dict):
    """
    合并嵌套对象和字典
    
    参数:
        base_obj: 基础嵌套对象
        env_dict: 环境特定嵌套字典
        
    返回:
        合并后的嵌套对象
    """
    # 创建一个新的嵌套对象
    nested_obj = type('NestedConfig', (), {})()
    
    # 复制基础对象的属性
    if hasattr(base_obj, 'as_dict'):
        base_dict = base_obj.as_dict()
    else:
        base_dict = {k: v for k, v in base_obj.__dict__.items() if not k.startswith('_')}
    
    # 先设置基础属性
    for key, value in base_dict.items():
        setattr(nested_obj, key, value)
    
    # 然后设置或覆盖环境特定属性
    for key, value in env_dict.items():
        if isinstance(value, dict):
            # 如果是嵌套字典，递归合并
            base_value = getattr(nested_obj, key, None)
            if base_value and (hasattr(base_value, 'as_dict') or hasattr(base_value, '__dict__')):
                # 如果基础对象中有相同的嵌套对象，递归合并
                merged = _merge_nested_dict(base_value, value)
                setattr(nested_obj, key, merged)
            else:
                # 否则创建新的嵌套对象
                sub_obj = type('NestedConfig', (), {})()
                for k, v in value.items():
                    setattr(sub_obj, k, v)
                setattr(nested_obj, key, sub_obj)
        else:
            # 直接覆盖
            setattr(nested_obj, key, value)
    
    return nested_obj


def _load_by_content(file_path):
    """
    尝试根据文件内容推断文件类型并加载
    
    参数:
        file_path: 配置文件的路径
        
    返回:
        一个包含配置项作为属性的配置对象
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            # 检查是否是JSON格式
            if content.startswith('{') and content.endswith('}'):
                try:
                    json.loads(content)
                    logger.info(f"根据内容判断为JSON格式: {file_path}")
                    return json_loader(file_path)
                except json.JSONDecodeError:
                    pass
            
            # 检查是否是YAML格式
            if ':' in content and not content.startswith('#'):
                try:
                    yaml.safe_load(content)
                    logger.info(f"根据内容判断为YAML格式: {file_path}")
                    return yaml_loader(file_path)
                except yaml.YAMLError:
                    pass
            
            # 检查是否是INI格式
            if '[' in content and ']' in content:
                try:
                    config = configparser.ConfigParser()
                    config.read_string(content)
                    if len(config.sections()) > 0:
                        logger.info(f"根据内容判断为INI格式: {file_path}")
                        return config_loader(file_path)
                except configparser.Error:
                    pass
            
            # 检查是否是ENV格式
            if '=' in content:
                logger.info(f"根据内容判断为ENV格式: {file_path}")
                return env_loader(file_path)
            
            # 如果无法识别，默认使用env_loader
            logger.warning(f"无法识别文件类型，默认使用env_loader: {file_path}")
            return env_loader(file_path)
    except Exception as e:
        logger.error(f"尝试加载配置文件时出错: {e}")
        # 返回一个空的配置对象
        return type('EmptyConfig', (), {
            'get': lambda self, key, default=None: default,
            'as_dict': lambda self: {},
            '__repr__': lambda self: "EmptyConfig()",
            '__getitem__': lambda self, key: None
        })()
