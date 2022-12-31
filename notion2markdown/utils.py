import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('notion2markdown')


def normalize_id(id: str) -> str:
    return id.replace('-', '')