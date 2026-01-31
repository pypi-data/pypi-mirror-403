import logging
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List

DEFAULT_LOGGING_BLACKLIST = [
    'PIL.PngImagePlugin',
    'matplotlib.font_manager'
]


def initialize_logging(
        *, rank: Optional[int] = None,
        log_filepath: Optional[str] = None,
        logging_format: str = '[%(asctime)s] %(filename)s:%(lineno)d - %(levelname)s: %(message)s',
        console_logging_level: int = logging.INFO,
        file_logging_level: int = logging.DEBUG,
        blacklist: Optional[List[str]] = DEFAULT_LOGGING_BLACKLIST,
) -> logging.Logger:
    """ Initializes the logging system.
    
    Args:
        rank (Optional[int]): The rank of the current process in a distributed setup.
            If None, assumes a single-process setup.
        log_filepath (Optional[str]): Path to the log file. If None, file logging is disabled.
        logging_format (str): The format string for log messages.
        console_logging_level (int): Logging level for console output.
        file_logging_level (int): Logging level for file output.
        blacklist (Optional[List[str]]): List of logger names to blacklist from logging.
        
    Returns:
        logging.Logger: Configured logger instance.
    
    Notes:
        You actually don't need to use the returned logger, as the root logger is configured.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Base logging level

    # Clear existing handlers to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # Include rank in log format if rank is provided
    if rank is not None:
        logging_format = f'[Rank {rank}]' + logging_format
    log_formatter = logging.Formatter(logging_format)

    # Custom filter to block messages from the blacklisted sources
    if blacklist is not None and len(blacklist) > 0:
        class BlacklistFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                return not any(record.name.startswith(src) for src in blacklist)

        blacklist_filter = BlacklistFilter()

    else:
        blacklist_filter = None

    # Only the main process (rank 0) logs to console to avoid clutter
    if rank is None or rank == 0:
        handler_console = logging.StreamHandler()
        handler_console.setFormatter(log_formatter)
        handler_console.setLevel(console_logging_level)

        if blacklist_filter is not None:
            handler_console.addFilter(blacklist_filter)

        logger.addHandler(handler_console)

    if log_filepath:
        # Each rank logs to its own file to prevent write conflicts
        if rank is not None:
            assert rank >= 0
            filename, extension = os.path.splitext(log_filepath)
            log_filepath = f"{filename}_rank{rank}{extension}"

        handler_file = logging.FileHandler(
            filename=log_filepath, mode='a', encoding='utf-8'
        )
        handler_file.setFormatter(log_formatter)
        handler_file.setLevel(file_logging_level)

        if blacklist_filter is not None:
            handler_file.addFilter(blacklist_filter)

        logger.addHandler(handler_file)

    return logger


@dataclass
class AverageMetrics:
    sum: Dict[str, float] = field(default_factory=dict)
    count: Dict[str, int] = field(default_factory=dict)
    _averaged: Optional[Dict[str, float]] = None

    def reset(self):
        self.sum = {}
        self.count = {}
        self._averaged = None

    def update(self, **name2value: float):
        self._averaged = None
        for name, value in name2value.items():
            if name in self.sum:
                self.sum[name] += value
                self.count[name] += 1
            else:
                self.sum[name] = value
                self.count[name] = 1

    @property
    def averaged(self) -> Dict[str, float]:
        averaged = self._averaged
        if averaged is None:
            averaged = {}
            for name, value in self.sum.items():
                averaged[name] = value / self.count[name]
            self._averaged = averaged
        return averaged

    def summarize(self, number_formatter='{:.06f}') -> str:
        averaged = self.averaged
        return ' | '.join([f'{k}: ' + number_formatter.format(v) for k, v in averaged.items()])

    def state_dict(self) -> dict:
        return {
            'sum':   self.sum,
            'count': self.count,
        }

    def load_state_dict(self, state_dict: dict):
        self.sum = state_dict['sum']
        self.count = state_dict['count']
        self._averaged = None
