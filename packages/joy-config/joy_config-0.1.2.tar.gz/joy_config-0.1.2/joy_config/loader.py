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
    Automatically selects the appropriate loader to load configuration files based on file extension and environment.
    
    This function provides a flexible way to load configuration files by:
    1. Auto-detecting common configuration files if no path is specified
    2. Supporting environment-specific configurations (dev, test, prod)
    3. Merging base and environment-specific configurations
    4. Handling various file formats (YAML, JSON, INI/CFG, ENV)
    
    Args:
        config_path (str, optional): Path to the configuration file. If None, common configuration files 
                                     will be tried according to priority. Defaults to None.
        env (str, optional): Environment name (e.g., 'dev', 'test', 'prod'). If None, will try to get 
                             from environment variables. Defaults to None.
        
    Returns:
        object: A configuration object with configuration items as attributes.
    """
    # Determine the project root directory
    root_dir = _get_project_root()
    logger.debug(f"Project root directory: {root_dir}")
    
    # Determine the current environment
    if env is None:
        # Try to get environment name from environment variables
        env = os.environ.get('ENV', os.environ.get('ENVIRONMENT', os.environ.get('PROFILE', 'dev')))
    
    logger.info(f"Current environment: {env}")
    
    # If no configuration file path is specified, try common configuration files by priority
    if config_path is None:
        # Define common configuration files by priority, including environment-specific configuration files
        common_config_files = []
        
        # Environment-specific configuration files have higher priority
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
            
            # Also check the config directory
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
        
        # Then general configuration files
        common_config_files.extend([
            os.path.join(root_dir, ".env"),
            os.path.join(root_dir, "config.yaml"), os.path.join(root_dir, "config.yml"),
            os.path.join(root_dir, "config.json"),
            os.path.join(root_dir, "config.ini"), os.path.join(root_dir, "config.cfg"),
            os.path.join(root_dir, "application.yaml"), os.path.join(root_dir, "application.yml"),
            os.path.join(root_dir, "application.json"),
            os.path.join(root_dir, "application.properties"), os.path.join(root_dir, "application.ini")
        ])
        
        # Check for general configuration files in the config directory
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
        
        # Try to find existing configuration files
        for file_path in common_config_files:
            if os.path.exists(file_path):
                config_path = file_path
                logger.info(f"Auto-detected configuration file: {config_path}")
                break
        
        if config_path is None:
            logger.warning("No configuration file found, returning empty configuration")
            # Return an empty configuration object
            return type('EmptyConfig', (), {
                'get': lambda self, key, default=None: default,
                'as_dict': lambda self: {},
                '__repr__': lambda self: "EmptyConfig()",
                '__getitem__': lambda self, key: None
            })()
    else:
        # If the provided configuration path is a relative path, make it relative to the project root directory
        if not os.path.isabs(config_path):
            config_path = os.path.join(root_dir, config_path)
    
    # Load the base configuration
    base_config = _load_config_file(config_path)
    
    if env and config_path:
        # Infer the environment-specific configuration file path from the base configuration file path
        base_name, ext = os.path.splitext(config_path)
        
        # Special handling for .env file environment-specific naming convention
        if ext.lower() == '.env':
            env_config_path = f"{base_name}.{env}"
        else:
            env_config_path = f"{base_name}-{env}{ext}"
        
        # If the environment-specific configuration file exists, load and merge it
        if os.path.exists(env_config_path):
            logger.info(f"Loading environment-specific configuration file: {env_config_path}")
            env_config = _load_config_file(env_config_path)
            
            # Merge configurations
            base_config = _merge_configs(base_config, env_config)
            
    return base_config


def _get_project_root():
    """
    Attempts to determine the project's root directory.
    
    Uses multiple strategies to find the project root:
    1. Use the current working directory
    2. If running within a package, try to find the package's root directory
    3. Look up the directory tree for project marker files (setup.py, pyproject.toml, .git)
    
    Returns:
        str: The path to the project root directory
    """
    # Method 1: Use the current working directory
    cwd = os.getcwd()
    
    # Method 2: If running within a package, try to find the package's root directory
    try:
        # Get the main module from the call stack
        main_module = sys.modules['__main__']
        if hasattr(main_module, '__file__'):
            # The directory of the main module file might be the project root directory
            main_dir = os.path.dirname(os.path.abspath(main_module.__file__))
            
            # Check for typical project root directory markers
            if (os.path.exists(os.path.join(main_dir, 'setup.py')) or
                os.path.exists(os.path.join(main_dir, 'pyproject.toml')) or
                os.path.exists(os.path.join(main_dir, '.git'))):
                return main_dir
    except (KeyError, AttributeError):
        pass
    
    # Method 3: Look up the directory tree for project marker files
    path = Path(cwd)
    for p in [path] + list(path.parents):
        if (p / 'setup.py').exists() or (p / 'pyproject.toml').exists() or (p / '.git').exists():
            return str(p)
    
    # If no clear project root directory is found, return the current working directory
    return cwd


def _load_config_file(config_path):
    """
    Loads a configuration file based on its file extension.
    
    Determines the appropriate loader based on the file name pattern or extension,
    with special handling for .env files.
    
    Args:
        config_path (str): The path to the configuration file
        
    Returns:
        object: A configuration object containing the configuration items
    """
    # Get the file name (without path)
    file_name = os.path.basename(config_path.lower())
    
    # Use pattern matching to determine the file type
    if file_name == '.env' or file_name.startswith('.env.'):
        logger.info(f"Using env_loader to load: {config_path}")
        return env_loader(config_path)
    elif file_name.endswith('.yaml') or file_name.endswith('.yml'):
        logger.info(f"Using yaml_loader to load: {config_path}")
        return yaml_loader(config_path)
    elif file_name.endswith('.json'):
        logger.info(f"Using json_loader to load: {config_path}")
        return json_loader(config_path)
    elif file_name.endswith('.ini') or file_name.endswith('.cfg') or file_name.endswith('.properties'):
        logger.info(f"Using config_loader to load: {config_path}")
        return config_loader(config_path)
    else:
        # If the extension cannot be recognized, try to infer the file type from its content
        logger.info(f"Unrecognized file type: {file_name}, trying to infer from content")
        return _load_by_content(config_path)
    
    
def _merge_configs(base_config, env_config):
    """
    Merges two configuration objects.
    
    Creates a new configuration object that combines the base configuration and 
    environment-specific configuration, with the environment configuration taking precedence.
    
    Args:
        base_config (object): The base configuration object
        env_config (object): The environment-specific configuration object
        
    Returns:
        object: The merged configuration object
    """
    # Convert the environment configuration to a dictionary
    env_dict = env_config.as_dict() if hasattr(env_config, 'as_dict') else {}
    
    # Create a new configuration class
    class MergedConfig:
        def __init__(self, base, env_dict):
            self._base = base
            
            # Copy the attributes from the environment configuration to the new object
            for key, value in env_dict.items():
                if isinstance(value, dict):
                    # If it's a nested dictionary, recursively merge
                    base_value = getattr(base, key, None)
                    if base_value and hasattr(base_value, 'as_dict'):
                        # If there's a matching nested object in the base configuration, merge them
                        merged_obj = _merge_nested_dict(base_value, value)
                        setattr(self, key, merged_obj)
                    else:
                        # Otherwise create a new nested object
                        nested_obj = type('NestedConfig', (), {})()
                        for k, v in value.items():
                            setattr(nested_obj, k, v)
                        setattr(self, key, nested_obj)
                else:
                    # Directly override the base configuration
                    setattr(self, key, value)
        
        def get(self, key, default=None):
            """Gets a configuration item value, or returns the default if it doesn't exist"""
            # First try to get from the environment configuration
            try:
                if '.' in key:
                    parts = key.split('.')
                    obj = self
                    for part in parts[:-1]:
                        obj = getattr(obj, part, None)
                        if obj is None:
                            # If the intermediate path doesn't exist, fall back to the base configuration
                            return self._base.get(key, default)
                    return getattr(obj, parts[-1], None) or self._base.get(key, default)
                else:
                    return getattr(self, key, None) or self._base.get(key, default)
            except (AttributeError, KeyError):
                # If it doesn't exist in the environment configuration, fall back to the base configuration
                return self._base.get(key, default)
        
        def as_dict(self):
            """Converts all configuration items to a dictionary and returns it"""
            # First get the base configuration's dictionary
            result = self._base.as_dict() if hasattr(self._base, 'as_dict') else {}
            
            # Then add or override with the environment configuration's items
            for key, value in self.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, object) and not isinstance(value, (str, int, float, bool, list, dict)):
                        # If it's a nested object, recursively convert
                        nested_dict = {}
                        for attr in dir(value):
                            if not attr.startswith('_') and not callable(getattr(value, attr)):
                                attr_value = getattr(value, attr)
                                if isinstance(attr_value, object) and not isinstance(attr_value, (str, int, float, bool, list, dict)):
                                    # Recursively handle deeper nesting
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
            """Supports dictionary-style access: config['key'] or config['nested.key']"""
            if '.' in key:
                parts = key.split('.')
                obj = self
                for part in parts[:-1]:
                    try:
                        obj = getattr(obj, part)
                    except AttributeError:
                        # If not found in the environment configuration, try to get from the base configuration
                        try:
                            return self._base[key]
                        except (KeyError, AttributeError):
                            raise KeyError(part)
                try:
                    return getattr(obj, parts[-1])
                except AttributeError:
                    # If not found in the environment configuration, try to get from the base configuration
                    try:
                        return self._base[key]
                    except (KeyError, AttributeError):
                        raise KeyError(parts[-1])
            
            try:
                return getattr(self, key)
            except AttributeError:
                # If not found in the environment configuration, try to get from the base configuration
                try:
                    return self._base[key]
                except (KeyError, AttributeError):
                    raise KeyError(key)
    
    return MergedConfig(base_config, env_dict)


def _merge_nested_dict(base_obj, env_dict):
    """
    Merges a nested object and a dictionary.
    
    Creates a new nested object that combines the base nested object and 
    environment-specific nested dictionary, with the environment values taking precedence.
    
    Args:
        base_obj (object): The base nested object
        env_dict (dict): The environment-specific nested dictionary
        
    Returns:
        object: The merged nested object
    """
    # Create a new nested object
    nested_obj = type('NestedConfig', (), {})()
    
    # Copy the attributes from the base object
    if hasattr(base_obj, 'as_dict'):
        base_dict = base_obj.as_dict()
    else:
        base_dict = {k: v for k, v in base_obj.__dict__.items() if not k.startswith('_')}
    
    # First set the base attributes
    for key, value in base_dict.items():
        setattr(nested_obj, key, value)
    
    # Then set or override with environment-specific attributes
    for key, value in env_dict.items():
        if isinstance(value, dict):
            # If it's a nested dictionary, recursively merge
            base_value = getattr(nested_obj, key, None)
            if base_value and (hasattr(base_value, 'as_dict') or hasattr(base_value, '__dict__')):
                # If there's a matching nested object in the base object, recursively merge
                merged = _merge_nested_dict(base_value, value)
                setattr(nested_obj, key, merged)
            else:
                # Otherwise create a new nested object
                sub_obj = type('NestedConfig', (), {})()
                for k, v in value.items():
                    setattr(sub_obj, k, v)
                setattr(nested_obj, key, sub_obj)
        else:
            # Directly override
            setattr(nested_obj, key, value)
    
    return nested_obj


def _load_by_content(file_path):
    """
    Attempts to infer the file type from its content and load it.
    
    Examines the file content to determine if it's ENV, JSON, INI, or YAML format,
    then uses the appropriate loader.
    
    Args:
        file_path (str): The path to the configuration file
        
    Returns:
        object: A configuration object with configuration items as attributes
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            # First split the content into lines, and filter out empty lines and comment lines
            lines = [line.strip() for line in content.split('\n') 
                    if line.strip() and not line.strip().startswith('#')]
            
            if not lines:
                logger.warning(f"File content is empty or contains only comments: {file_path}")
                return type('EmptyConfig', (), {
                    'get': lambda self, key, default=None: default,
                    'as_dict': lambda self: {},
                    '__repr__': lambda self: "EmptyConfig()",
                    '__getitem__': lambda self, key: None
                })()
            
            # 1. Check if it's ENV format
            # ENV file characteristics: Most lines are in KEY=VALUE format, no obvious indentation structure
            env_line_pattern = r'^[A-Za-z_][A-Za-z0-9_]*='
            env_line_count = sum(1 for line in lines if '=' in line and not line.startswith('['))
            
            # If most non-empty lines are in KEY=VALUE format, it's likely an ENV file
            if env_line_count > 0 and env_line_count / len(lines) >= 0.5:
                logger.info(f"Determined to be ENV format based on content: {file_path}")
                return env_loader(file_path)
            
            # 2. Check if it's JSON format
            # JSON file characteristics: Starts with {, ends with }, and is a valid JSON structure
            if content.startswith('{') and content.endswith('}'):
                try:
                    json.loads(content)
                    logger.info(f"Determined to be JSON format based on content: {file_path}")
                    return json_loader(file_path)
                except json.JSONDecodeError:
                    pass
            
            # 3. Check if it's INI format
            # INI file characteristics: Contains lines in [section] format, and can be parsed by ConfigParser
            if any(line.startswith('[') and line.endswith(']') for line in lines):
                try:
                    config = configparser.ConfigParser()
                    config.read_string(content)
                    if len(config.sections()) > 0:
                        logger.info(f"Determined to be INI format based on content: {file_path}")
                        return config_loader(file_path)
                except configparser.Error:
                    pass
            
            # 4. Check if it's YAML format
            # YAML file characteristics: Contains indentation structure, key-value pairs use colons (with a space after)
            yaml_indicators = [
                line for line in lines 
                if ': ' in line and not (line.startswith('{') or line.startswith('['))
            ]
            
            # Check if there's an indentation structure (typical YAML characteristic)
            has_indentation = any(line.startswith(' ') or line.startswith('\t') for line in lines)
            
            if (yaml_indicators or has_indentation) and not any(line.startswith('[') and line.endswith(']') for line in lines):
                try:
                    yaml_data = yaml.safe_load(content)
                    if yaml_data is not None:  # Ensure successful parsing
                        logger.info(f"Determined to be YAML format based on content: {file_path}")
                        return yaml_loader(file_path)
                except yaml.YAMLError:
                    pass
            
            # 5. If none of the above match, but the file contains equals signs, try loading as ENV file
            if any('=' in line for line in lines):
                logger.info(f"File type not clearly identified, but contains equals signs, trying as ENV format: {file_path}")
                return env_loader(file_path)
            
            # 6. Last fallback: Try loading as YAML
            try:
                yaml_data = yaml.safe_load(content)
                if yaml_data is not None:
                    logger.info(f"File type not clearly identified, trying as YAML format: {file_path}")
                    return yaml_loader(file_path)
            except yaml.YAMLError:
                pass
            
            # If all attempts fail, default to using env_loader
            logger.warning(f"Could not identify file type, defaulting to env_loader: {file_path}")
            return env_loader(file_path)
            
    except Exception as e:
        logger.error(f"Error trying to load configuration file: {e}")
        # Return an empty configuration object
        return type('EmptyConfig', (), {
            'get': lambda self, key, default=None: default,
            'as_dict': lambda self: {},
            '__repr__': lambda self: "EmptyConfig()",
            '__getitem__': lambda self, key: None
        })()