import logging
import sys
from typing import Dict, Any
from pythonjsonlogger import jsonlogger
from core.config import get_settings

settings = get_settings()

class StructuredFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record['service'] = settings.APP_NAME
        log_record['version'] = settings.APP_VERSION
        log_record['environment'] = settings.ENVIRONMENT
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id

def setup_logging() -> None:
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    formatter = StructuredFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logging.basicConfig(
        level=log_level,
        handlers=[handler],
        format='%(message)s'
    )
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('redis').setLevel(logging.WARNING)