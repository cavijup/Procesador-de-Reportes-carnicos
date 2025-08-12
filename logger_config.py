# logger_config.py
import logging
import sys

def setup_logger():
    """
    Configura y devuelve un logger estandarizado para la aplicación.
    """
    # Evita añadir múltiples handlers si la función se llama más de una vez
    if logging.getLogger("app_logger").hasHandlers():
        return logging.getLogger("app_logger")

    # Crear el logger
    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.INFO)

    # Crear un handler para enviar logs a la consola (terminal)
    handler = logging.StreamHandler(sys.stdout)
    
    # Crear un formato para los mensajes de log
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Añadir el handler al logger
    logger.addHandler(handler)
    
    return logger

# Instanciar el logger para que esté disponible para importación
logger = setup_logger()