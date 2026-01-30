import os
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path


class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.isoformat()


def setup_logger(name: str = "agentgog", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure file logger
    
    Args:
        name: Logger name
        log_file: Path to log file (defaults to ~/agentgog_smol.log)
    
    Returns:
        Configured logger
    """
    if log_file is None:
        log_file = os.path.expanduser("~/agentgog_smol.log")
    
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(CustomFormatter("[LOG] %(asctime)s|%(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def log_event(**kwargs):
    """
    Log an event in a bash-parseable format
    
    Args:
        **kwargs: Key-value pairs to log
    """
    kwargs_str = "|".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
    logging.info(kwargs_str)


def get_model_idshort(model_id: str) -> str:
    """
    Return short model name
    
    Args:
        model_id: Full model identifier
    
    Returns:
        Short model name
    """
    return model_id.split("/")[-1].split(":")[0]
