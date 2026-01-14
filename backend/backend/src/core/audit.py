import logging
from datetime import datetime
from typing import Dict, Any, Optional
from core.config import get_settings
import json

settings = get_settings()

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
    async def log_auth_event(
        self,
        event_type: str,
        user_id: str,
        client_ip: str,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        audit_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "client_ip": client_ip,
            "service": settings.APP_NAME,
            "environment": settings.ENVIRONMENT
        }
        if additional_data:
            audit_data.update(additional_data)
        self.logger.info(json.dumps(audit_data))

audit_logger = AuditLogger()