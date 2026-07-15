import logging
import sys
import os

def setup_logger(name="credit_app"):
    """
    Configures a professional logger that outputs to both console and a log file.
    """
    logger = logging.getLogger(name)
    
    # If logger already has handlers, don't add them again
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s (line %(lineno)d): %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # File Handler
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    return logger
