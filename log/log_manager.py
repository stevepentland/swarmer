import logging


class LogManager:
    BASE_LOGGER = logging.getLogger('gunicorn.error')
    TEMPLATE = '{name}: {message}'

    def __init__(self, name: str):
        self._name = name

    def info(self, message):
        self.BASE_LOGGER.info(self.fill_template(message))

    def debug(self, message):
        self.BASE_LOGGER.debug(self.fill_template(message))

    def error(self, message):
        self.BASE_LOGGER.error(self.fill_template(message))

    def fill_template(self, message):
        return self.TEMPLATE.format(name=self._name, message=message)
