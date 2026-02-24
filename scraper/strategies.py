from abc import ABC, abstractmethod
from client import ScraperClient
from parser import IncrementalParser, BackFillParser
import os


class ScraperStrategy(ABC):
    @abstractmethod
    def get_data(self):
        pass


class IncrementalStrategy(ScraperStrategy):
    def __init__(self):
        self.client=ScraperClient()
        self.parser=IncrementalParser()
        self.URL=os.getenv("INCREMENTAL_SOURCE_URL")

    def get_data(self):
        raw_data=self.client.fetch_data(self.URL)
        return self.parser.parse(raw_data)

class BackFillStrategy(ScraperStrategy):
    def __init__(self):
        self.client=ScraperClient()
        self.parser=BackFillParser()
