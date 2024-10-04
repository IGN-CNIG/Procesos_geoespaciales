from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import logging.config
from pathlib import Path

from schema import Schema, And, Use, SchemaError

# Define the schema for configuration validation
CONFIG_SCHEMA = Schema({
    'version': And(Use(int), lambda n: n > 0),
    'disable_existing_loggers': Use(bool),
    'formatters': {
        'brief': {
            'format': And(Use(str)),
            'encoding': And(Use(str), lambda s: s in ['utf-8', 'iso-8859-1'])  # Valid encodings
        },
        'precise': {
            'format': And(Use(str)),
            'datefmt': And(Use(str)),
            'encoding': And(Use(str), lambda s: s in ['utf-8', 'iso-8859-1'])  # Valid encodings
        }
    },
    'handlers': {
        'console': {
            'class': And(Use(str)),
            'formatter': And(Use(str)),
            'level': And(Use(str)),
            'stream': And(Use(str))
        },
        'file': {
            'class': And(Use(str)),
            'formatter': And(Use(str)),
            'filename': And(Use(str)),
            'encoding': And(Use(str), lambda s: s in ['utf-8', 'iso-8859-1']),  # Valid encodings
            'maxBytes': And(Use(int), lambda x: x > 0),
            'backupCount': And(Use(int), lambda x: x >= 0)
        },
        'email': {
            'class': And(Use(str)),
            'mailhost': And(Use(str)),
            'fromaddr': And(Use(str)),
            'toaddrs': [And(Use(str))],
            'subject': And(Use(str))
        }
    },
    'loggers': {
        'src.modules.inspire': {
            'level': And(Use(str)),
            'handlers': [And(Use(str))]
        },
        'src.modules.capabilities': {
            'level': And(Use(str)),
            'handlers': [And(Use(str))]
        },
        'src.modules.database': {
            'level': And(Use(str)),
            'handlers': [And(Use(str))]
        }
    }
})

DEFAULT_CONFIG = {
            'version': 1, 
            'disable_existing_loggers': False, # https://docs.python.org/3/howto/logging.html#configuring-logging
            'formatters': 
            {
                'brief': {'format': '%(message)s'}, 
                'precise': {
                    'format': '%(asctime)s %(levelname)-8s %(name)-15s %(message)s', 
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                }
            }, 
            'handlers': 
            {
                'console': {
                    'class': 'logging.StreamHandler', 
                    'formatter': 'brief', 
                    'level': 'INFO', 
                    'stream': 'ext://sys.stdout'
                }, 
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler', 
                    'formatter': 'precise', 
                    'filename': 'logs/logging.log', 
                    'encoding': 'iso-8859-1',
                    'maxBytes': 20*1024*1024, # 20MB
                    'backupCount': 3
                }, 
                'email': {
                    'class': 'logging.handlers.SMTPHandler', 
                    'mailhost': 'localhost', 
                    'fromaddr': 'user@gmail.com', 
                    'toaddrs': ['user1@gmail.com', 'user2@gmail.com'], 
                    'subject': 'TEST EMAIL'}
            },
            'loggers': {}
        }

class Logger:
    """
    Creates and manages a logger with handlers that can be enabled or disabled dynamically.

    This class sets up a logger with different handlers (e.g., console, file, email), 
    and allows enabling/disabling of specific handlers and loggers at runtime. The logger 
    configuration can be customized.

    Attributes:
        logger_name (str): The name of the logger being managed.
        level (str): The logging level.
        handlers (List[str]): List of active handlers for the logger.
        config (Dict): Dictionary holding the logging configuration.

    ## Methods
        enable_handler(handler_name: str): 
            Enables a specific handler for the logger (e.g., 'console', 'file').
        disable_handler(handler_name: str): 
            Disables a specific handler for the logger.
        set_level(level: str): 
            Sets the logging level for the logger.
        disable_logger(logger_name: str): 
            Disables the logger for the current instance, preventing it from generating log messages.
        enable_logger(logger_name: str):
            Enables the logger for the current instance, allowing it to generate log messages.
        update_config(new_config: Dict[str, Any]) -> None:
            Updates the logging configuration with a new configuration dictionary after validating it.

    Example:
    >>> log = Logger('src.inspire', 'DEBUG', ['console', 'file'])
    >>> log.enable_handler('email')
    >>> log.disable_handler('console')
    >>> log.logger.info("This is an info log message.")
    >>> log.set_level('ERROR')
    >>> new_config = {
        ...     'version': 1,
        ...     'disable_existing_loggers': False,
        ...     'formatters': {
        ...         'brief': {'format': '%(message)s'},
        ...         'precise': {'format': '%(asctime)s %(levelname)-8s %(name)-15s %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
        ...     },
        ...     'handlers': {
        ...         'console': {'class': 'logging.StreamHandler', 'formatter': 'brief', 'level': 'INFO', 'stream': 'ext://sys.stdout'}
        ...     },
        ...     'loggers': {
        ...         'src.inspire': {'level': 'DEBUG', 'handlers': ['console']}
        ...     }
        ... }
        >>> log.update_config(new_config)
    """
    def __init__(self, logger_name: Optional[str] = __name__, level: Optional[str] = 'INFO', handlers: Optional[List[str]] = ['console']) -> None:
        """
        Initializes the Logger instance with the specified logger name, logging level, and handlers.

        This sets up the logging configuration for the logger, applying formatters, handlers, and 
        ensuring log files are created with dynamic filenames based on the logger name and current date.

        Parameters:
            logger_name (Optional[str]): The name of the logger being managed. Defaults to __name__.
            level (Optional[str]): The logging level (e.g., 'INFO', 'DEBUG'). Defaults to 'INFO'.
            handlers (Optional[List[str]]): List of handlers to activate for the logger (e.g., ['console', 'file']). Defaults to ['console'].
        """
        self.logger_name = logger_name
        self.level = level
        self.handlers = handlers
        self.config = DEFAULT_CONFIG.copy()

        # Setup logger config
        self._initialize_logger()

    def _initialize_logger(self) -> None:
        """
        Initializes the logger with the configured handlers and settings.

        This method modifies the filename for the file handler to include the current date and 
        logger name, and ensures the required directories are created if they don't exist. It 
        then configures the logger based on the updated configuration.
        """
        # Modify the file handler filename to include the date and logger name
        Path('logs').mkdir(parents=True, exist_ok=True)
        for handler_name, handler in self.config['handlers'].items():
            if handler_name == 'file':
                filename = self.logger_name.replace('src.modules.', '')
                today = datetime.today().strftime('%Y%m%d')
                handler['filename'] = f'logs/{filename}_{today}.log'
                self._create_dir(handler['filename'])

        # Set up the logger
        self.config['loggers'] = {
            self.logger_name: {
                'level': self.level,
                'handlers': self.handlers
            }
        }

        logging.config.dictConfig(self.config)
        self.__logger = logging.getLogger(self.logger_name)

    def _create_dir(self, filename: str) -> None:
        """
        Creates the parent directory for the log file if it does not exist.

        Parameters:
            filename (str): The full path to the log file.

        Example:
        >>> log = Logger(__name__)
        >>> log._create_dir('logs/inspire.log')
        """
        if filename and not Path(filename).parent.exists():
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

    def enable_handler(self, handler_name: str) -> None:
        """
        Enable a specific handler for the logger.

        Parameters:
            handler_name (str): The name of the handler to enable (e.g., 'console', 'file', 'email').

        Example:
        >>> log = Logger(__name__)
        >>> log.enable_handler('email')
        """
        if handler_name not in self.handlers and handler_name in self.config['handlers']:
            self.handlers.append(handler_name)
            self._initialize_logger()

    def disable_handler(self, handler_name: str) -> None:
        """
        Disable a specific handler for the logger.

        Parameters:
            handler_name (str): The name of the handler to disable (e.g., 'console', 'file', 'email').

        Example:
        >>> log = Logger('src.inspire')
        >>> log.disable_handler('console')
        """
        if handler_name in self.handlers:
            self.handlers.remove(handler_name)
            self._initialize_logger()

    def set_level(self, level: str) -> None:
        """
        Set the logging level for the logger.

        Parameters:
            level (str): The new logging level (e.g., 'DEBUG', 'INFO', 'WARNING').

        Example:
            >>> log = Logger('src.inspire')
            >>> log.set_level('DEBUG')
        """
        self.level = level
        self._initialize_logger()
        
    def disable_logger(self) -> None:
        """
        Disables the logger for the current instance, preventing it from generating log messages.

        This method targets the logger specified by the `logger_name` attribute of the class and 
        sets its `disabled` attribute to `True`.

        Example:
        >>> log = Logger('src.inspire')
        >>> log.disable_logger()
        """
        logger = logging.getLogger(self.logger_name)
        logger.disabled = True

    def enable_logger(self) -> None:
        """
        Enables the logger for the current instance, allowing it to generate log messages.

        This method targets the logger specified by the `logger_name` attribute of the class and 
        sets its `disabled` attribute to `False`, making it active again.

        Example:
            >>> log = Logger('src.inspire')
            >>> log.enable_logger()
            >>> log.logger.info("This log will be displayed.")
        """
        logger = logging.getLogger(self.logger_name)
        logger.disabled = False
        
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Updates the logging configuration with a new configuration dictionary after validating it.

        This method validates the new configuration dictionary against a predefined schema and 
        applies it if it is valid. If the schema validation fails, a `SchemaError` is raised.

        Parameters:
            new_config (Dict[str, Any]): The new configuration dictionary to apply.

        Raises:
            SchemaError: If the new configuration dictionary does not conform to the schema.

        Example:
            >>> new_config = {
            ...     'version': 1,
            ...     'disable_existing_loggers': False,
            ...     'formatters': {
            ...         'brief': {'format': '%(message)s'},
            ...         'precise': {'format': '%(asctime)s %(levelname)-8s %(name)-15s %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
            ...     },
            ...     'handlers': {
            ...         'console': {'class': 'logging.StreamHandler', 'formatter': 'brief', 'level': 'INFO', 'stream': 'ext://sys.stdout'}
            ...     },
            ...     'loggers': {
            ...         'src.ServiceReaders': {'level': 'DEBUG', 'handlers': ['console']}
            ...     }
            ... }
            >>> log.update_config(new_config)
        """
        # Validate the new configuration against the schema
        try:
            CONFIG_SCHEMA.validate(new_config)
        except SchemaError as e:
            raise ValueError(f"Configuration validation failed: {e}")

        # Update the configuration and reinitialize the logger
        self.config.update(new_config)
        self._initialize_logger()

    @property
    def logger(self):
        return self.__logger