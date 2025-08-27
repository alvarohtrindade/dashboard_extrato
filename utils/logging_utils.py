"""
Módulo de logging padronizado conforme CLAUDE.md
Thread-safe logging com múltiplos níveis e saídas
"""
import os
import logging
import threading
import sys
from enum import Enum
from typing import Optional
from pathlib import Path

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO  
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class Log:
    _lock = threading.Lock()
    _loggers = {}
    _console_output = True
    _log_file = None
    _level = LogLevel.INFO
    _formatter = None
    
    @classmethod  
    def set_level(cls, level):
        """Define o nível de logging - aceita LogLevel enum ou logging constants"""
        if hasattr(level, 'value'):
            level = level.value
        with cls._lock:
            cls._level = level
            for logger in cls._loggers.values():
                logger.setLevel(level)
    
    @classmethod
    def set_console_output(cls, enabled: bool):
        with cls._lock:
            cls._console_output = enabled
    
    @classmethod
    def set_log_file(cls, file_path: str, append: bool = True):
        with cls._lock:
            cls._log_file = file_path
            
            # Criar diretório se não existir
            log_dir = Path(file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        with cls._lock:
            if name not in cls._loggers:
                logger = logging.getLogger(name)
                logger.setLevel(cls._level.value)
                logger.handlers.clear()
                
                # Formatter padrão
                if cls._formatter is None:
                    cls._formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                
                # Console handler
                if cls._console_output:
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setFormatter(cls._formatter)
                    console_handler.setLevel(cls._level.value)
                    logger.addHandler(console_handler)
                
                # File handler
                if cls._log_file:
                    try:
                        file_handler = logging.FileHandler(cls._log_file, mode='a' if True else 'w')
                        file_handler.setFormatter(cls._formatter)
                        file_handler.setLevel(cls._level.value)
                        logger.addHandler(file_handler)
                    except Exception as e:
                        # Fallback para stderr
                        fallback_handler = logging.StreamHandler(sys.stderr)
                        fallback_handler.setFormatter(cls._formatter)
                        logger.addHandler(fallback_handler)
                        # Fallback silencioso para stderr em caso de erro de log file
                
                cls._loggers[name] = logger
            
            return cls._loggers[name]