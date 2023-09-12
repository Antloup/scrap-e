import threading
import time
from typing import List, Type, Callable, Optional
import scrapy
from PyQt5 import QtCore
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from crochet import setup
import yaml
import sys
from utils.paths import absolute_path, scrapers_rel_path, img_data_path

setup()


class ScraperPool(QtCore.QObject):

    finish = QtCore.pyqtSignal()
    update = QtCore.pyqtSignal(int, list)

    def __init__(self, spiders: List[Type[scrapy.Spider]], blocking_start: bool = False,
                 config_file: str = scrapers_rel_path, **kwargs):
        super().__init__()
        self.status_lock = threading.Lock()
        config_path = absolute_path(config_file)
        self.config = yaml.load(open(config_path), Loader=yaml.FullLoader)
        self.spiders_status = dict()
        self.blocking_start = blocking_start
        kwargs['status_lock'] = self.status_lock
        kwargs['callback'] = self.spider_finish
        kwargs['status_function'] = self.update_status
        self.kwargs = kwargs
        self.spiders = spiders
        self.custom_settings = {
            'IMAGES_STORE': img_data_path,
            'FILES_STORE': img_data_path,
            'AUTOTHROTTLE_ENABLED': True,
            # 'AUTOTHROTTLE_ENABLED': False,
            'LOG_ENABLED': False,
            # 'LOG_ENABLED': True,
            'LOG_LEVEL': 'DEBUG',  # CRITICAL, ERROR, WARNING, INFO, DEBUG
            # 'LOG_FILE': 'TEST.LOG',
            'ITEM_PIPELINES': {
                'scrapy_ext.pipelines.MyImagesPipeline': 1,
                # 'scrapy.contrib.pipeline.images.ImagesPipeline': 1,
                'scrapy_ext.pipelines.PeeweePipeline': 10
            },
            'EXTENSIONS': {
                'scrapy.extensions.feedexport.FeedExporter': None,
            },
            'DOWNLOAD_DELAY': 11.42,
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0'
        }

        self.process = CrawlerRunner(settings=self.custom_settings)

    def start(self):
        for spider in self.spiders:
            self.spiders_status[spider.name] = False

        for spider in self.spiders:
            config: dict = self.config[spider.name] if spider.name in self.config else None
            self.process.crawl(spider, config=config, **self.kwargs)

        if self.blocking_start:
            while not self.all_spiders_finish():
                time.sleep(1.0)

    def spider_finish(self, spider=scrapy.Spider):
        print('Scraper Pool finish')
        if self.status_lock is not None:
            self.status_lock.acquire()
        self.spiders_status[spider.name] = True
        if self.all_spiders_finish():
            self.finish.emit()
        if self.status_lock is not None:
            self.status_lock.release()

    def all_spiders_finish(self) -> bool:
        for spider in self.spiders:
            if not self.spiders_status[spider.name]:
                return False
        return True

    def update_status(self, status: int, data: List):
        self.update.emit(status, data)
