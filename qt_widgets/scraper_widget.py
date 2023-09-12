from typing import List

from PyQt5.QtWidgets import QWidget, QPushButton, QProgressBar, QHBoxLayout, QGridLayout, QGroupBox, QVBoxLayout

from global_vars import ScraperStatus
from scrapers import ScraperPool
from scrapers.deal import EbaySpider, LbcSpider, ParuvenduSpider


class ScraperWidget(QWidget):

    def __init__(self):

        super().__init__()

        # Properties
        self.scrapers: List = [EbaySpider, LbcSpider, ParuvenduSpider]
        self.scraper_group_box = QGroupBox('Scraper')
        self.scraper_start_button = QPushButton('Start scrap')
        self.scraper_progress_bar = QProgressBar()

        # Init
        line_layout = QHBoxLayout()
        self.scraper_start_button.clicked.connect(self.start_scrap)
        line_layout.addWidget(self.scraper_start_button)

        self.scraper_progress_bar.setMaximum(1)
        self.scraper_progress_bar.setValue(0)
        self.scraper_progress_bar.setEnabled(True)
        self.scraper_progress_bar.setMaximumWidth(300)
        line_layout.addWidget(self.scraper_progress_bar)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.scraper_group_box.setLayout(line_layout)
        main_layout.addWidget(self.scraper_group_box)
        self.setLayout(main_layout)

    def start_scrap(self):
        scraper = ScraperPool(self.scrapers, keep_update=True)
        scraper.finish.connect(self.scrap_done)
        scraper.update.connect(self.print_scraper_log)
        self.scraper_start_button.setEnabled(False)
        self.scraper_progress_bar.setEnabled(True)
        self.scraper_progress_bar.setMaximum(0)
        self.scraper_progress_bar.setValue(0)
        scraper.start()

    def scrap_done(self):
        self.scraper_start_button.setEnabled(True)
        self.scraper_progress_bar.setEnabled(False)
        self.scraper_progress_bar.setMaximum(1)
        self.scraper_progress_bar.setValue(0)
        print('Scrap done !')

    def print_scraper_log(self, status: int, data: List) -> None:
        if status == ScraperStatus.MESSAGE:
            print(data[0])
        elif status == ScraperStatus.AMOUNT_PAGES:
            self.scraper_progress_bar.setMaximum(self.scraper_progress_bar.maximum() + data[0])
        elif status == ScraperStatus.PAGE_DONE:
            self.scraper_progress_bar.setValue(self.scraper_progress_bar.value() + 1)
        elif status == ScraperStatus.PAGE_SKIP:
            self.scraper_progress_bar.setValue(self.scraper_progress_bar.value() + data[0])
