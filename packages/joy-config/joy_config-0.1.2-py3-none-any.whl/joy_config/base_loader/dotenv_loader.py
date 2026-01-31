from loguru import logger

def dotenv_loader(env_path=".env"):
    """
    加载.env文件中的环境变量，并将这些变量作为返回对象的属性
    
    参数:
        env_path: .env文件的路径，默认为当前目录下的.env文件
        
    返回:
        一个包含环境变量作为属性的EnvConfig对象
    """
    class EnvConfig:
        """
        存储环境变量的配置类
        """
        def __init__(self, env_file):
            self._env_file = env_file
            self._load_env()
        
        def _load_env(self):
            """加载环境变量文件"""
            try:
                with open(self._env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # 跳过空行和注释行
                        if not line or line.startswith('#'):
                            continue
                            
                        # 解析键值对
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # 去除值两边的引号（如果有）
                            if (value.startswith('"') and value.endswith('"')) or \
                               (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                                
                            # 将环境变量设置为对象的属性
                            setattr(self, key, value)
            except FileNotFoundError:
                logger.error(f"can't find the env file '{self._env_file}'")
            except Exception as e:
                logger.error(f"can't load the env file : {e}")
        
        def get(self, key, default=None):
            """获取环境变量值，如果不存在则返回默认值"""
            return getattr(self, key, default)
        
        def as_dict(self):
            """将所有环境变量转换为字典返回"""
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        
        def __repr__(self):
            attrs = ', '.join(f"{key}={repr(value)}" for key, value in self.__dict__.items() 
                             if not key.startswith('_'))
            return f"EnvConfig({attrs})"
        
        def __getitem__(self, key):
            """支持字典式访问: config['KEY']"""
            try:
                return getattr(self, key)
            except AttributeError:
                raise KeyError(key)
    
    return EnvConfig(env_path)