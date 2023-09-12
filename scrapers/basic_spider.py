import threading
from typing import Optional, Callable, List

import scrapy
from scrapy import signals
from pydispatch import dispatcher


class BasicSpider(scrapy.Spider):

    def __init__(self, status_lock: Optional[threading.Lock] = None, callback: Optional[Callable] = None,
                 status_function: Optional[Callable[[int, List], None]] = None, **kwargs):
        super().__init__(**kwargs)
        self.status_lock = status_lock
        self.callback = callback if callback is not None else lambda x: None
        self.status_function = status_function if status_function is not None else self.default_status_function
        dispatcher.connect(self.callback, signals.spider_closed)

    @staticmethod
    def default_status_function(status: int, data: List):
        print(str(status), data)

    def send_status(self, status:int, data: List):
        if self.status_lock is not None:
            self.status_lock.acquire()
        self.status_function(status, data)
        if self.status_lock is not None:
            self.status_lock.release()
