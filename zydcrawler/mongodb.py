from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
import logging

logger = logging.getLogger(__name__)


class MongoDB:

    def __init__(self, url, config={}):

        self.config = config
        self.url = url 

        self._connection()

    def _connection(self):
        try:
            self.client = MongoClient(self.url, **self.config)
            
        except (ConfigurationError, ConnectionFailure) as e:

            logger.debug(f"[MONGO-CONNECTION] connection failed: {str(e)}")
    