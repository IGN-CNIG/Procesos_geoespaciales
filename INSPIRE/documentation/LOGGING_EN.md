# Logger Module Documentation

## Overview

The `Logger` class provides a robust mechanism to manage and configure logging in Python applications. It allows dynamic enabling/disabling of log handlers, changing log levels, and updating logging configurations based on a defined schema. 

It supports multiple handlers, including console, file, and email, and ensures that logging configuration can be customized easily.

### Schema for Configuration Validation

The logging configuration is validated using a schema defined by the `schema` module. This ensures that any new configuration applied to the logger conforms to the expected structure and types.

```python
CONFIG_SCHEMA = Schema({
    'version': And(Use(int), lambda n: n > 0),
    'disable_existing_loggers': Use(bool),
    'formatters': {
        'brief': {
            'format': And(Use(str)),
            'encoding': And(Use(str), lambda s: s in ['utf-8', 'iso-8859-1'])
        },
        'precise': {
            'format': And(Use(str)),
            'datefmt': And(Use(str)),
            'encoding': And(Use(str), lambda s: s in ['utf-8', 'iso-8859-1'])
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
            'encoding': And(Use(str), lambda s: s in ['utf-8', 'iso-8859-1']),
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
        'src.ServiceReaders': {
            'level': And(Use(str)),
            'handlers': [And(Use(str))]
        },
        'src.Databases': {
            'level': And(Use(str)),
            'handlers': [And(Use(str))]
        },
        'src.Reports': {
            'level': And(Use(str)),
            'handlers': [And(Use(str))]
        }
    }
})
```
### Default Logging Configuration
A default configuration is provided to simplify the logger's initialization. It includes console, file, and email handlers, with basic formatting.

```python
DEFAULT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'brief': {'format': '%(message)s'},
        'precise': {
            'format': '%(asctime)s %(levelname)-8s %(name)-15s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
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
            'maxBytes': 20 * 1024 * 1024,  # 20MB
            'backupCount': 3
        },
        'email': {
            'class': 'logging.handlers.SMTPHandler',
            'mailhost': 'localhost',
            'fromaddr': 'user@gmail.com',
            'toaddrs': ['user1@gmail.com', 'user2@gmail.com'],
            'subject': 'TEST EMAIL'
        }
    },
    'loggers': {}
}
```

## Classes

### Logger
The Logger class allows for dynamic configuration and management of logging.

#### Attributes
  - `logger_name` (str): The name of the logger being managed.
  - `level` (str): The logging level (e.g., DEBUG, INFO, etc.).
  - `handlers` (List[str]): List of active handlers (e.g., console, file, email).
  - `config` (Dict[str, Any]): The current logging configuration.

#### Methods
  - **`enable_handler(self, handler_name: str) -> None`**: Enables a specific handler for the logger (e.g., console, file, email).
  - **`disable_handler(self, handler_name: str) -> None`**: Disables a specific handler for the logger.
  - **`set_level(self, level: str) -> None`**: Changes the logging level (e.g., DEBUG, INFO).
  - **`disable_logger(self) -> None`**: Disables the logger, preventing it from generating log messages.
  - **`enable_logger(self) -> None`**: Re-enables the logger to allow it to generate log messages.
  - **`update_config(self, new_config: Dict[str, Any]) -> None`**: Updates the logger's configuration based on a new configuration dictionary, after validating it with the CONFIG_SCHEMA.

#### Example
```python
Copiar código
from datetime import datetime
log = Logger('src.inspire', 'DEBUG', ['console', 'file'])
# Enable an email handler
log.enable_handler('email')
# Disable console handler
log.disable_handler('console')
# Log a message
log.logger.info("This is an info log message.")
# Change the logging level to ERROR
log.set_level('ERROR')
# Update configuration dynamically
new_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'brief': {'format': '%(message)s'},
        'precise': {
            'format': '%(asctime)s %(levelname)-8s %(name)-15s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'brief',
            'level': 'INFO',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'src.ServiceReaders': {
            'level': 'DEBUG',
            'handlers': ['console']
        }
    }
}
log.update_config(new_config)
```