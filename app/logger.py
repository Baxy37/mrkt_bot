import logging
from app.config import Config

def setup_logger():
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            # можно добавить FileHandler для сохранения в файл
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()
