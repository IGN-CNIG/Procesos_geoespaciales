# Documentación del módulo Logger

## Resumen

La clase `Logger` proporciona un mecanismo robusto para gestionar y configurar el registro en aplicaciones de Python. Permite habilitar/deshabilitar dinámicamente los controladores de registro, cambiar los niveles de registro y actualizar las configuraciones de registro según un esquema definido.

Admite múltiples controladores, incluidos consola, archivo y correo electrónico, y garantiza que la configuración de registro se pueda personalizar fácilmente.

### Esquema para la Validación de Configuración

La configuración de registro se valida utilizando un esquema definido por el módulo `schema`. Esto asegura que cualquier nueva configuración aplicada al logger se ajuste a la estructura y tipos esperados.

### Configuración de Registro Predeterminada

Se proporciona una configuración predeterminada para simplificar la inicialización del logger. Incluye controladores de consola, archivo y correo electrónico, con un formato básico.

## Clases

### Logger

La clase Logger permite la configuración y gestión dinámica del registro.

#### Atributos
  - `logger_name` (str): El nombre del logger que se está gestionando.
  - `level` (str): El nivel de registro (por ejemplo, DEBUG, INFO, etc.).
  - `handlers` (List[str]): Lista de controladores activos (por ejemplo, consola, archivo, correo electrónico).
  - `config` (Dict[str, Any]): La configuración actual del registro.

#### Métodos
  - **`enable_handler(self, handler_name: str) -> None`**: Habilita un controlador específico para el logger (por ejemplo, consola, archivo, correo electrónico).
  - **`disable_handler(self, handler_name: str) -> None`**: Deshabilita un controlador específico para el logger.
  - **`set_level(self, level: str) -> None`**: Cambia el nivel de registro (por ejemplo, DEBUG, INFO).
  - **`disable_logger(self) -> None`**: Desactiva el logger, impidiendo que genere mensajes de registro.
  - **`enable_logger(self) -> None`**: Vuelve a habilitar el logger para permitir que genere mensajes de registro.
  - **`update_config(self, new_config: Dict[str, Any]) -> None`**: Actualiza la configuración del logger según un nuevo diccionario de configuración, después de validarlo con el `CONFIG_SCHEMA`.

#### Ejemplo
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