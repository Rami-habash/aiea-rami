import os
import yaml
from dotenv import load_dotenv

load_dotenv()

# Load configuratioso n file and convert to environment variables


def load_yaml(yaml_file: str) -> dict:
    with open(yaml_file, 'r', encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # openai api key
    for key, value in config.items():
        if isinstance(value, dict) and "api_key" in value:
            env_val = os.getenv(value["api_key"])
            if env_val:
                config[key]["api_key"] = env_val
    for key, value in config["agent"].items():
        model_type = value['type']
        config["agent"][key]["api_key"] = config[model_type]["api_key"]
        config["agent"][key]["base_url"] = config[model_type]["base_url"]
    return config


# Set default configuration file path
DEFAULT_CONFIG_PATH = "./config/config.yaml"
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = f"{project_path}/config/config.yaml"

# Get configuration file path
config_file_path = os.getenv('CONFIG_FILE_PATH', DEFAULT_CONFIG_PATH)
# print(f"Config file path: {config_file_path}")

# Load configuration file and convert to environment variables
config = load_yaml(config_file_path)
# print(config)
