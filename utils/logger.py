import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(name: str = "trade_simulator") -> logging.Logger:
    """
    Set up a custom logger with both file and console handlers.
    
    Args:
        name: Name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_websocket_error(logger: logging.Logger, error: Exception):
    """Log WebSocket related errors"""
    logger.error(f"WebSocket Error: {str(error)}")

def log_tick_delay(logger: logging.Logger, delay_ms: float):
    """Log tick processing delay"""
    logger.info(f"Tick Processing Delay: {delay_ms:.2f}ms")

def log_inference_time(logger: logging.Logger, model_name: str, time_ms: float):
    """Log model inference time"""
    logger.info(f"{model_name} Inference Time: {time_ms:.2f}ms")

def log_ui_update(logger: logging.Logger, update_time_ms: float):
    """Log UI update time"""
    logger.info(f"UI Update Time: {update_time_ms:.2f}ms") 