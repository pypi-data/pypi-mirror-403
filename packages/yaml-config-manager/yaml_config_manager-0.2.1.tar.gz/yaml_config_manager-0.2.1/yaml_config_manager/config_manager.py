import yaml
import sys
import re

# Custom YAML Loader to handle scientific notation correctly (e.g., 1e-4)
class CustomSafeLoader(yaml.SafeLoader):
    pass

# Regex to match scientific notation floats like 1e-4, 1.0e-4, -1E4
# This pattern matches optional sign, digits, optional dot, optional digits, and mandatory exponent part
# OR digits with mandatory dot and optional exponent.
# Essentially we want to catch what YAML 1.1 catches but 1.2 might miss or what PyYAML misses by default.
CustomSafeLoader.add_implicit_resolver(
    u'tag:yaml.org,2002:float',
    re.compile(r'''^(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+]?[0-9]+)?
                    |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
                    |\.[0-9_]+(?:[eE][-+][0-9]+)?
                    |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*
                    |[-+]?\.(?:inf|Inf|INF)
                    |\.(?:nan|NaN|NAN))$''', re.X),
    list(u'-+0123456789.')
)

class Config(dict):
    """
    A dictionary that allows access to keys as attributes.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = Config(v)
            elif isinstance(v, list):
                self[k] = [Config(i) if isinstance(i, dict) else i for i in v]

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'Config' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

    def to_dict(self):
        """
        Recursively converts Config objects back to standard dictionaries.
        """
        result = {}
        for k, v in self.items():
            if isinstance(v, Config):
                result[k] = v.to_dict()
            elif isinstance(v, list):
                result[k] = [i.to_dict() if isinstance(i, Config) else i for i in v]
            else:
                result[k] = v
        return result

    def update_from_flat_dict(self, flat_dict):
        """
        Updates the config from a flat dictionary with dotted keys.
        e.g. {'server.port': 9000} -> config.server.port = 9000
        """
        for key, value in flat_dict.items():
            keys = key.split('.')
            d = self
            for i, k in enumerate(keys[:-1]):
                if k not in d:
                    # Create nested Config if it doesn't exist
                    d[k] = Config()
                elif not isinstance(d[k], dict):
                    # If we encounter a non-dict value on the path, we might need to overwrite it
                    # or error out. Overwriting seems safer for "add params" behavior.
                    d[k] = Config()
                d = d[k]
            d[keys[-1]] = value

def convert_value(value):
    """
    Robust conversion of string values to appropriate types.
    """
    if not isinstance(value, str):
        return value
        
    s_lower = value.lower()
    # Booleans
    if s_lower in ('true', 'yes', 'on', 't', 'y'):
        return True
    if s_lower in ('false', 'no', 'off', 'f', 'n'):
        return False
    
    # Null/None
    if s_lower in ('none', 'null', 'nil'):
        return None

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    return value

def parse_cli_args(args_list):
    """
    Manually parse CLI arguments to support both --key=value and --key value styles.
    Returns:
        config_path (str or None): path to config file if found
        overrides (dict): dictionary of overrides
    """
    config_path = None
    overrides = {}
    
    i = 0
    while i < len(args_list):
        arg = args_list[i]
        
        # Check if it is a flag
        if arg.startswith('--'):
            # Strip leading dashes
            key_part = arg.lstrip('-')
            
            # Check for = in the flag itself
            if '=' in key_part:
                key, val_str = key_part.split('=', 1)
                
                # Special case for --config
                if key == 'config':
                    config_path = val_str
                else:
                    overrides[key] = convert_value(val_str)
                i += 1
            else:
                key = key_part
                
                # Look ahead for value
                # A value is considered any token that doesn't start with '--'
                # Exception: negative numbers might start with -, but usually not --
                # To be safe, we assume next arg is value if it doesn't start with --
                
                has_next = (i + 1 < len(args_list))
                next_arg = args_list[i+1] if has_next else None
                
                # Determine if next_arg is a value or another flag
                if has_next and not next_arg.startswith('--'):
                    val_str = next_arg
                    
                    if key == 'config':
                        config_path = val_str
                    else:
                        overrides[key] = convert_value(val_str)
                    i += 2
                else:
                    # Flag without value (boolean flag)
                    # Cannot apply to --config
                    if key == 'config':
                         raise ValueError("--config requires a file path")
                    
                    # Implicitly True
                    overrides[key] = True
                    i += 1
        else:
            # Positional argument or unflagged argument
            # For now, ignore them to allow compatibility with other parsers/scripts
            # that might take positional args.
            i += 1
            
    return config_path, overrides

def load_config(config_path=None, args=None):
    """
    Loads configuration from a YAML file and overrides with CLI arguments.
    
    Args:
        config_path (str, optional): Default config path. Overridden by CLI --config.
        args (list, optional): List of arguments to parse. Defaults to sys.argv[1:].
    """
    if args is None:
        args = sys.argv[1:]
        
    cli_config_path, cli_overrides = parse_cli_args(args)
    
    # CLI --config takes precedence over function argument
    final_config_path = cli_config_path if cli_config_path else config_path
    
    config = Config()
    
    if final_config_path:
        with open(final_config_path, 'r') as file:
            # Use CustomSafeLoader
            file_data = yaml.load(file, Loader=CustomSafeLoader)
            if file_data:
                config = Config(file_data)
    
    # Apply overrides
    config.update_from_flat_dict(cli_overrides)
    
    return config

def save_config(config, filepath):
    """
    Saves the config object to a YAML file.
    """
    data = config.to_dict() if isinstance(config, Config) else config
    with open(filepath, 'w') as file:
        yaml.dump(data, file)

def load_config_from_file(filepath):
    """
    Helper to load just a file without CLI args.
    """
    with open(filepath, 'r') as file:
        config = yaml.load(file, Loader=CustomSafeLoader)
    return Config(config)
