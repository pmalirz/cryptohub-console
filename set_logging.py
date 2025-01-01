import logging
import sys
import colorlog
from datetime import datetime
from pathlib import Path

def setup_logging():
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Get the root logger and set its level to DEBUG
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Define emoji for different log levels
    log_emojis = {
        'DEBUG': '🔍 ',
        'INFO': '✨ ',
        'WARNING': '⚠️ ',
        'ERROR': '❌ ',
        'CRITICAL': '🚨 '
    }

    class EmojiFormatter(logging.Formatter):
        def format(self, record):
            # Add emoji prefix based on log level
            record.emoji = log_emojis.get(record.levelname, '')
            return super().format(record)

    # ----------------------------
    # File Handler (with timestamps and emoji)
    # ----------------------------
    log_filename = f"cryptotaxpl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(logs_dir / log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = EmojiFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(emoji)s%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # ----------------------------
    # Console Handler (with colors and emoji)
    # ----------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s%(reset)s - %(emoji)s%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white'
        },
        reset=True,
        style='%'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger