"""Configuration handling for lumpy_log output formats."""

import os
import yaml
from pathlib import Path

DEFAULT_OUTPUT_FORMAT = "obsidian"
VALID_FORMATS = {"obsidian", "devlog", "docx"}

# Default values for all config options
DEFAULTS = {
    'output_format': DEFAULT_OUTPUT_FORMAT,
    'outputfolder': 'devlog',
    'changelog': False,
    'verbose': False,
    'raw_output': False,
    'raw_test_output': False,
    'force': False,
    'dryrun': False,
    'render_code_as_images': False,
}

def _load_config_file(repo_path: str = ".") -> dict:
    """Load .lumpyconfig.yml from repo_path if present."""
    config_file = Path(repo_path) / ".lumpyconfig.yml"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: could not read {config_file}: {e}")
            return {}
    return {}

def get_config_value(key: str, args: dict, repo_path: str = ".", default=None):
    """Get a config value from CLI args or config file.
    
    Args:
        key: Config key name
        args: CLI arguments dict
        repo_path: Repository path for config file lookup
        default: Default value if not found (uses DEFAULTS if not provided)
        
    Returns:
        Config value from CLI args (priority), config file, or default
    """
    # CLI args have highest priority
    if key in args and args.get(key) is not None:
        return args[key]
    
    # Config file second priority
    config = _load_config_file(repo_path)
    if key in config:
        return config[key]
    
    # Default value
    if default is not None:
        return default
    return DEFAULTS.get(key)

def get_output_format(args: dict, repo_path: str = ".") -> list:
    """Determine output format(s) from CLI args and config file.
    
    Args:
        args: CLI arguments dict
        repo_path: Repository path for config file lookup
        
    Returns:
        List of output formats: ["obsidian"], ["devlog"], ["docx"], or combinations
    """
    # Load config file
    config = _load_config_file(repo_path)
    config_formats = config.get("output_format", DEFAULT_OUTPUT_FORMAT)
    if isinstance(config_formats, str):
        config_formats = [config_formats]
    
    # CLI args override config
    if args.get("output_format"):
        cli_formats = args["output_format"]
        if isinstance(cli_formats, str):
            cli_formats = [cli_formats]
        return [f for f in cli_formats if f in VALID_FORMATS] or [DEFAULT_OUTPUT_FORMAT]
    
    return [f for f in config_formats if f in VALID_FORMATS] or [DEFAULT_OUTPUT_FORMAT]


def get_raw_output(args: dict, repo_path: str = ".", default: bool = False) -> bool:
    """Determine whether to include raw test output.

    Precedence: CLI raw_test_output -> CLI raw_output -> config raw_test_output ->
    config raw_output -> default.
    """
    if args.get("raw_test_output") is not None:
        return bool(args["raw_test_output"])
    if args.get("raw_output") is not None:
        return bool(args["raw_output"])

    config = _load_config_file(repo_path)
    if "raw_test_output" in config:
        return bool(config.get("raw_test_output"))
    if "raw_output" in config:
        return bool(config.get("raw_output"))

    return bool(default)

def get_hcti_credentials(repo_path: str = ".") -> dict:
    """Get HCTI API credentials from config file or environment variables.
    
    Environment variables take precedence over config file.
    
    Args:
        repo_path: Repository path for config file lookup
        
    Returns:
        Dict with 'user_id' and 'api_key' keys, or empty dict if not found
    """
    # Try environment variables first (highest priority)
    env_user_id = os.environ.get('HCTI_API_USER_ID')
    env_api_key = os.environ.get('HCTI_API_KEY')
    
    if env_user_id and env_api_key:
        return {
            'user_id': env_user_id,
            'api_key': env_api_key,
            'source': 'environment'
        }
    
    # Try config file
    config = _load_config_file(repo_path)
    config_user_id = config.get('hcti_api_user_id')
    config_api_key = config.get('hcti_api_key')
    
    if config_user_id and config_api_key:
        return {
            'user_id': config_user_id,
            'api_key': config_api_key,
            'source': 'config file'
        }
    
    return {}

def print_active_config(args: dict, repo_path: str = "."):
    """Print all active configuration values showing source (CLI/config/default).
    
    Args:
        args: CLI arguments dict
        repo_path: Repository path for config file lookup
    """
    print("=" * 60)
    print("Active Configuration:")
    print("=" * 60)
    
    config_file = _load_config_file(repo_path)
    
    # Define config keys to display
    config_keys = [
        ('output_format', 'Output format(s)'),
        ('outputfolder', 'Output folder'),
        ('verbose', 'Verbose mode'),
        ('limit', 'Entry limit'),
        ('changelog', 'Changelog order'),
        ('render_code_as_images', 'Code blocks as images in docx output'),
        ('force', 'Force overwrite of change logs'),
        ('dryrun', 'Dry run mode'),
        ('from_commit', 'From commit'),
        ('to_commit', 'To commit'),
    ]
    
    for key, label in config_keys:
        # Determine value and source
        cli_value = args.get(key)
        config_value = config_file.get(key)
        default_value = DEFAULTS.get(key)
        
        if cli_value is not None:
            value = cli_value
            source = "CLI"
        elif config_value is not None:
            value = config_value
            source = "config file"
        else:
            value = default_value
            source = "default"
        
        # Skip if None and no default
        if value is None:
            continue
            
        print(f"  {label:.<30} {value!r:20} [{source}]")

    # Handle raw test output (honors both raw_test_output and raw_output aliases)
    raw_effective = get_raw_output(args, repo_path, DEFAULTS.get('raw_output', False))
    raw_cli = args.get('raw_test_output', args.get('raw_output'))
    raw_cfg = config_file.get('raw_test_output', config_file.get('raw_output'))
    if raw_cli is not None:
        raw_source = 'CLI'
    elif raw_cfg is not None:
        raw_source = 'config file'
    else:
        raw_source = 'default'
    print(f"  {'Raw test output':.<30} {raw_effective!r:20} [{raw_source}]")
    
    # Show HCTI credentials status
    hcti_creds = get_hcti_credentials(repo_path)
    if hcti_creds:
        hcti_status = f"configured ({hcti_creds.get('source')})"
    else:
        hcti_status = "not configured"
    print(f"  {'HCTI API credentials':.<30} {hcti_status:20} [status]")
    
    print("=" * 60)
    print()
