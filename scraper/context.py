from strategies import ScraperStrategy
from repository import ScraperRepository


class ScraperContext:
    def __init__(self, strategy: ScraperStrategy, repository: ScraperRepository):
        self.strategy=strategy
        self.repository=repository

    def execute(self):
        data=self.strategy.get_data()
        self.repository.save_all(data)