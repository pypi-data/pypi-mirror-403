"""
SDK Router Tools — collection of utility tools for automation pipelines.

Tools included:
- telegram: Rate-limited Telegram message sender with priority queue support
- logging: Rich-powered logger with file persistence
- html: HTML cleaner for LLM pipelines
"""

__version__ = "0.1.2"

# Telegram exports
from .telegram import (
    # Exceptions
    TelegramError,
    TelegramConfigError,
    TelegramSendError,
    # Queue
    MessagePriority,
    TelegramMessageQueue,
    telegram_queue,
    # Types
    ParseMode,
    # Formatters
    EMOJI_MAP,
    format_to_yaml,
    format_message_with_context,
    # Shortcuts
    send_error,
    send_success,
    send_warning,
    send_info,
    send_stats,
    send_alert,
    # Service
    TelegramSender,
    # Utils
    send_telegram_message,
    send_telegram_photo,
    send_telegram_document,
)

# Logging exports
from .logging import (
    get_logger,
    setup_logging,
    find_project_root,
    get_log_dir,
    reset_logging,
    LogLevel,
)

# HTML Cleaner exports (main API)
from .html import (
    # Primary API
    HTMLCleaner,
    CleanerConfig,
    CleanerResult,
    CleanerStats,
    ChunkInfo,
    OutputFormat,
    clean,
    clean_to_json,
    # Pipeline
    CleaningPipeline,
    PipelineConfig,
    PipelineResult,
    clean_html,
    clean_for_llm,
)

__all__ = [
    "__version__",
    # Telegram - Exceptions
    "TelegramError",
    "TelegramConfigError",
    "TelegramSendError",
    # Telegram - Queue
    "MessagePriority",
    "TelegramMessageQueue",
    "telegram_queue",
    # Telegram - Types
    "ParseMode",
    # Telegram - Formatters
    "EMOJI_MAP",
    "format_to_yaml",
    "format_message_with_context",
    # Telegram - Shortcuts
    "send_error",
    "send_success",
    "send_warning",
    "send_info",
    "send_stats",
    "send_alert",
    # Telegram - Service
    "TelegramSender",
    # Telegram - Utils
    "send_telegram_message",
    "send_telegram_photo",
    "send_telegram_document",
    # Logging
    "get_logger",
    "setup_logging",
    "find_project_root",
    "get_log_dir",
    "reset_logging",
    "LogLevel",
    # Cleaner - Primary API
    "HTMLCleaner",
    "CleanerConfig",
    "CleanerResult",
    "CleanerStats",
    "ChunkInfo",
    "OutputFormat",
    "clean",
    "clean_to_json",
    # Cleaner - Pipeline
    "CleaningPipeline",
    "PipelineConfig",
    "PipelineResult",
    "clean_html",
    "clean_for_llm",
]
