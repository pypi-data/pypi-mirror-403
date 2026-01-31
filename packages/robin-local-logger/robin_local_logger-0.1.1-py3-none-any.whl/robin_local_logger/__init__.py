import os
import json
import logging
from typing import Optional
from .handler import RobinFileHandler

class RobinJSONFormatter(logging.Formatter):
    """Formatter that outputs log records as JSON strings."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def init_robin_logger(app=None, *, log_file: str = "robin.log", max_mb: float = 5.0, logger_name: str = "robin_logger", api_key: Optional[str] = None, port: Optional[int] = None):
    """Initialize the robin logger.

    If 'app' is provided, it mounts routes on that FastAPI instance.
    If 'app' is None, it creates a new FastAPI instance.
    If 'port' is provided, it starts a Uvicorn server on that port.
    """
    try:
        from fastapi import FastAPI, APIRouter, Body, Depends, HTTPException, status
        from fastapi.security import APIKeyHeader
    except ImportError:
        raise ImportError("FastAPI is required to use robin_local_logger integration.")

    if app is None:
        app = FastAPI(title="Robin Standalone Logger")

    # Ensure directory exists
    parent = os.path.dirname(log_file)
    if parent:
        os.makedirs(parent, exist_ok=True)

    handler = RobinFileHandler(log_file, max_mb=max_mb)
    handler.setFormatter(RobinJSONFormatter())

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Capture system logs
    for name in ["fastapi", "uvicorn", "uvicorn.access", "uvicorn.error"]:
        l = logging.getLogger(name)
        l.addHandler(handler)

    # State handles
    if not hasattr(app, "state"):
        # Minimal state mock for non-FastAPI objects if necessary,
        # but since we created a FastAPI app above, it has state.
        pass

    setattr(app.state, "robin_logger", logger)
    setattr(app.state, "robin_log_file", log_file)
    setattr(app.state, "robin_log_handler", handler)

    router = APIRouter()

    async def verify_api_key(
        x_api_key: str = Depends(APIKeyHeader(name="X-API-Key", auto_error=False))
    ):
        if api_key and x_api_key != api_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate API Key",
            )
        return x_api_key

    @router.get("/robin/logs", dependencies=[Depends(verify_api_key)])
    async def get_logs(lines: int = 200):
        if not os.path.exists(log_file):
            return {"logs": []}
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            selected = all_lines[-lines:]
            parsed_logs = []
            for line in selected:
                try:
                    parsed_logs.append(json.loads(line))
                except json.JSONDecodeError:
                    parsed_logs.append({"raw": line.strip()})
            return {"logs": parsed_logs}
        except Exception as e:
            return {"error": str(e)}

    @router.post("/robin/logs", dependencies=[Depends(verify_api_key)])
    async def post_logs(payload: dict = Body(...)):
        message = payload.get("message") or payload.get("msg") or str(payload)
        level = (payload.get("level") or "info").lower()
        log = getattr(app.state, "robin_logger")
        if not hasattr(log, level):
            level = "info"
        getattr(log, level)(message)
        return {"status": "ok"}

    app.include_router(router)

    if port is not None:
        import uvicorn
        logger.info(f"Starting standalone Robin server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)

    return app
