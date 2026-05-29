"""Convenience entrypoint: `python run.py` starts the API server."""
import uvicorn

from app.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("Starting API server on http://0.0.0.0:8000")
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=False)
