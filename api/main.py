import uvicorn

from rag.api.app import create_app
from rag.config.settings import get_settings
from rag.config.logging_config import setup_logging

setup_logging()
app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("main:app", host="0.0.0.0", port=settings.app_port, reload=True)
