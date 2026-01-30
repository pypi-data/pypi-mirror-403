import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """Configures and returns a logger for the SDK."""
    logger = logging.getLogger(f"gudb.{name}")
    
    # Only add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(levelname)s] gudb | %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    return logger
