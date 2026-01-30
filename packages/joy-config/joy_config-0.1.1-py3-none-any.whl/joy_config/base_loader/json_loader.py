import os
import json

from loguru import logger

def json_loader(json_path="config.json"):
    """
    加载JSON格式的配置文件，并将配置项作为返回对象的属性
    
    参数:
        json_path: JSON配置文件的路径，默认为当前目录下的config.json文件
        
    返回:
        一个包含配置项作为属性的JsonConfig对象
    """
    class JsonConfig:
        """
        存储JSON配置项的配置类
        """
        def __init__(self, json_file):
            self._json_file = json_file
            self._load_json()
        
        def _load_json(self):
            """加载JSON配置文件"""
            try:
                if not os.path.exists(self._json_file):
                    logger.error(f"can't find the JSON file '{self._json_file}'")
                    return
                
                with open(self._json_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 将JSON数据转换为对象属性
                self._set_attributes(config_data)
            except json.JSONDecodeError as e:
                logger.error(f"invalid JSON format in '{self._json_file}': {e}")
            except Exception as e:
                logger.error(f"can't load the JSON file: {e}")
        
        def _set_attributes(self, data, parent=None):
            """递归设置属性"""
            if parent is None:
                parent = self
                
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        # 为嵌套字典创建新对象
                        nested_obj = type('NestedConfig', (), {})()
                        setattr(parent, key, nested_obj)
                        self._set_attributes(value, nested_obj)
                    else:
                        setattr(parent, key, value)
        
        def get(self, key, default=None):
            """获取配置项值，如果不存在则返回默认值"""
            # 如果包含点，表示访问嵌套属性
            if '.' in key:
                parts = key.split('.')
                obj = self
                for part in parts[:-1]:
                    obj = getattr(obj, part, None)
                    if obj is None:
                        return default
                return getattr(obj, parts[-1], default)
            return getattr(self, key, default)
        
        def as_dict(self):
            """将所有配置项转换为字典返回"""
            result = {}
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
            return f"JsonConfig({', '.join(attrs)})"
        
        def __getitem__(self, key):
            """支持字典式访问: config['key'] 或 config['nested.key']"""
            if '.' in key:
                parts = key.split('.')
                obj = self
                for part in parts[:-1]:
                    try:
                        obj = getattr(obj, part)
                    except AttributeError:
                        raise KeyError(part)
                try:
                    return getattr(obj, parts[-1])
                except AttributeError:
                    raise KeyError(parts[-1])
            try:
                return getattr(self, key)
            except AttributeError:
                raise KeyError(key)
    
    return JsonConfig(json_path)


