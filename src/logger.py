import logging.config
import json

def setup_logging(default_path='src/logging.json', default_level=logging.INFO):
    """Setup logging configuration"""
    try:
        with open(default_path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    except Exception as e:
        print(f"Error in logging configuration: {e}")
        logging.basicConfig(level=default_level)
