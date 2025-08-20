import logging
import os
import yaml

def setup_logging(config_path='config.yaml'):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        log_cfg = config.get('logging', {})
        log_level = getattr(logging, log_cfg.get('level', 'INFO').upper(), logging.INFO)
        log_file = log_cfg.get('file')
        handlers = [logging.StreamHandler()]
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            handlers.append(logging.FileHandler(log_file))
        logging.basicConfig(level=log_level, handlers=handlers,
                            format='%(asctime)s %(levelname)s %(name)s %(message)s')
    else:
        logging.basicConfig(level=logging.INFO)

# Usage: import and call setup_logging() at the start of your main scripts.
