import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for the given module name.
    
    Args:
        name: The name of the module (typically __name__)
        
    Returns:
        A configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    return logger

def singleton(cls):
    """
    A decorator that implements the Singleton design pattern.
    
    Ensures that a class has only one instance and provides a global point of 
    access to it. Subsequent calls to the decorated class will return the 
    same instance.
    
    Args:
        cls: The class to be decorated.
        
    Returns:
        The singleton instance of the class.
    """
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance