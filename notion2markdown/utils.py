import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('notion2markdown')


def normalize_id(id: str) -> str:
    return id.replace('-', '')


def get_whitespace(line, leading=True):
    if leading:
        stripped = line.lstrip()
        return line[:-len(stripped)], stripped
    stripped = line.rstrip()
    return line[len(stripped):], stripped