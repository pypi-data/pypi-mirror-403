import logging
import os
import logging_loki

def setup_loki_logging():
    """
    Configures the timescaler logger to stream logs to Loki.
    LOKI_URL environment variable is used, defaulting to http://localhost:3100/loki/api/v1/push
    """
    loki_url = os.getenv("LOKI_URL", "http://localhost:3100/loki/api/v1/push")
    
    handler = logging_loki.LokiHandler(
        url=loki_url,
        tags={"application": "timescaler"},
        version="1",
    )
    
    logger = logging.getLogger("timescaler")
    # Avoid adding duplicate handlers if setup is called multiple times
    for h in logger.handlers:
        if isinstance(h, logging_loki.LokiHandler):
            return

    logger.addHandler(handler)
    logger.setLevel(logging.INFO) # Ensure level allows info logs
