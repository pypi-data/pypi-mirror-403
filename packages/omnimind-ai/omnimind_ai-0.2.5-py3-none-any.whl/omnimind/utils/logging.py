"""
OMNIMIND Structured Logging
Production-ready logging with multiple handlers and formats

Usage:
    from omnimind.utils.logging import get_logger, setup_logging
    
    logger = get_logger(__name__)
    logger.info("Training started", extra={"epoch": 1, "lr": 0.001})
    
    # Or setup global logging
    setup_logging(level="DEBUG", log_file="omnimind.log")
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
from functools import lru_cache


# ==================== Log Levels ====================

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

DEFAULT_LOG_LEVEL = os.environ.get("OMNIMIND_LOG_LEVEL", "INFO").upper()
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ==================== Custom Formatters ====================

class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    def __init__(self, fmt: str = None, datefmt: str = None, use_colors: bool = True):
        super().__init__(fmt or DEFAULT_LOG_FORMAT, datefmt or DEFAULT_DATE_FORMAT)
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors:
            color = self.COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            record.name = f"{self.BOLD}{record.name}{self.RESET}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add standard fields
        log_data["module"] = record.module
        log_data["function"] = record.funcName
        log_data["line"] = record.lineno
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


# ==================== Custom Logger ====================

class OmnimindLogger(logging.Logger):
    """Extended logger with structured logging support"""
    
    def _log_with_extra(
        self,
        level: int,
        msg: str,
        args: tuple,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        if extra:
            kwargs.setdefault("extra", {})["extra_data"] = extra
        super()._log(level, msg, args, **kwargs)
    
    def debug(self, msg: str, *args, extra: Dict[str, Any] = None, **kwargs):
        self._log_with_extra(logging.DEBUG, msg, args, extra, **kwargs)
    
    def info(self, msg: str, *args, extra: Dict[str, Any] = None, **kwargs):
        self._log_with_extra(logging.INFO, msg, args, extra, **kwargs)
    
    def warning(self, msg: str, *args, extra: Dict[str, Any] = None, **kwargs):
        self._log_with_extra(logging.WARNING, msg, args, extra, **kwargs)
    
    def error(self, msg: str, *args, extra: Dict[str, Any] = None, **kwargs):
        self._log_with_extra(logging.ERROR, msg, args, extra, **kwargs)
    
    def critical(self, msg: str, *args, extra: Dict[str, Any] = None, **kwargs):
        self._log_with_extra(logging.CRITICAL, msg, args, extra, **kwargs)


# Set custom logger class
logging.setLoggerClass(OmnimindLogger)


# ==================== Logger Factory ====================

@lru_cache(maxsize=128)
def get_logger(name: str) -> OmnimindLogger:
    """
    Get or create a logger with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured OmnimindLogger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Processing started", extra={"batch_size": 32})
    """
    logger = logging.getLogger(name)
    
    # Only add handlers if none exist
    if not logger.handlers:
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)
        
        # Set level from environment
        level = LOG_LEVELS.get(DEFAULT_LOG_LEVEL, logging.INFO)
        logger.setLevel(level)
    
    return logger


def setup_logging(
    level: Union[str, int] = None,
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
    json_format: bool = False,
    colored: bool = True,
) -> None:
    """
    Setup global logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_dir: Directory for log files (optional)
        json_format: Use JSON format for file logging
        colored: Use colored output for console
        
    Example:
        setup_logging(level="DEBUG", log_file="omnimind.log")
    """
    # Determine level
    if level is None:
        level = DEFAULT_LOG_LEVEL
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger("omnimind")
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(use_colors=colored))
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file or log_dir:
        if log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            log_file = log_path / f"omnimind_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        
        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT))
        
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)
        
        root_logger.info(f"Logging to file: {log_file}")


# ==================== Specialized Loggers ====================

def get_training_logger() -> OmnimindLogger:
    """Get logger for training operations"""
    return get_logger("omnimind.training")


def get_inference_logger() -> OmnimindLogger:
    """Get logger for inference operations"""
    return get_logger("omnimind.inference")


def get_model_logger() -> OmnimindLogger:
    """Get logger for model operations"""
    return get_logger("omnimind.model")


def get_storage_logger() -> OmnimindLogger:
    """Get logger for storage operations"""
    return get_logger("omnimind.storage")


# ==================== Context Managers ====================

class LogContext:
    """Context manager for adding context to log messages"""
    
    def __init__(self, logger: OmnimindLogger, **context):
        self.logger = logger
        self.context = context
        self._original_extra = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def info(self, msg: str, **extra):
        combined = {**self.context, **extra}
        self.logger.info(msg, extra=combined)
    
    def debug(self, msg: str, **extra):
        combined = {**self.context, **extra}
        self.logger.debug(msg, extra=combined)
    
    def warning(self, msg: str, **extra):
        combined = {**self.context, **extra}
        self.logger.warning(msg, extra=combined)
    
    def error(self, msg: str, **extra):
        combined = {**self.context, **extra}
        self.logger.error(msg, extra=combined)


# ==================== Utility Functions ====================

def log_model_info(model, logger: OmnimindLogger = None):
    """Log model information"""
    if logger is None:
        logger = get_model_logger()
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    logger.info(
        "Model loaded",
        extra={
            "total_params": total_params,
            "trainable_params": trainable_params,
            "total_params_m": f"{total_params / 1e6:.1f}M",
            "trainable_params_m": f"{trainable_params / 1e6:.1f}M",
        }
    )


def log_training_step(
    step: int,
    loss: float,
    lr: float,
    logger: OmnimindLogger = None,
    **metrics
):
    """Log training step metrics"""
    if logger is None:
        logger = get_training_logger()
    
    logger.info(
        f"Step {step}: loss={loss:.4f}, lr={lr:.2e}",
        extra={
            "step": step,
            "loss": loss,
            "learning_rate": lr,
            **metrics
        }
    )


def log_inference_stats(
    tokens_generated: int,
    time_seconds: float,
    logger: OmnimindLogger = None,
):
    """Log inference statistics"""
    if logger is None:
        logger = get_inference_logger()
    
    tokens_per_second = tokens_generated / time_seconds if time_seconds > 0 else 0
    
    logger.info(
        f"Generated {tokens_generated} tokens in {time_seconds:.2f}s ({tokens_per_second:.1f} tok/s)",
        extra={
            "tokens_generated": tokens_generated,
            "time_seconds": time_seconds,
            "tokens_per_second": tokens_per_second,
        }
    )


# ==================== Module Initialization ====================

# Create default omnimind logger
_root_logger = get_logger("omnimind")
