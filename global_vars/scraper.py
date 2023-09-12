from dataclasses import dataclass


@dataclass
class ScraperStatus:
    labels = []
    OTHER = 0
    MESSAGE = 1
    AMOUNT_PAGES = 2
    PAGE_DONE = 3
    PAGE_SKIP = 4
    END = 5
    ERROR = 6

ScraperStatus.labels = [key.replace('_',' ') for key, value in vars(ScraperStatus).items() if not key.startswith('__') and key.upper() == key]
