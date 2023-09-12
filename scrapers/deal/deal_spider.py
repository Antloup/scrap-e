import re
from typing import List, Optional, Union, Tuple

from global_vars.ebay import Listing, Category
from global_vars.scraper import ScraperStatus
from guesser.guesser import Guesser
from models import Deal
from scrapers import BasicSpider
from datetime import date, datetime
import scrapy
import locale
from global_vars.model import Website, Category as ModelCategory, ReferenceValue
from abc import ABC, abstractmethod


class DealUrl(ABC):

    def __init__(self, url: str, search: dict, page: int = 1):
        self.url = url
        self.search = search
        self.category = self.search['category']
        self.add_category(self.category)
        self.page = page
        self.page_number(page)
        self.keywords: str = ''

    @abstractmethod
    def sort_by(self, sort: int):
        return self

    @abstractmethod
    def add_listing(self, listing: str):
        return self

    @abstractmethod
    def add_conditions(self, conditions: List[int]):
        return self

    @abstractmethod
    def add_keywords(self, keywords: Optional[str]):
        if keywords is not None:
            self.keywords = keywords
        return self

    @abstractmethod
    def add_category(self, category: int):
        return self

    @abstractmethod
    def add_price(self, high: int = -1, low: int = -1):
        return self

    @abstractmethod
    def page_number(self, page_num: int):
        self.page = page_num
        return self

    def remove_page(self, page_keyword: str):
        regex = r'&' + page_keyword + '=[\w]+(&|$)'
        self.url = re.sub(regex, '', self.url)
        return self

    def __str__(self):
        return 'keywords {} | page {}'.format(self.keywords if self.keywords != '' else 'ALL', self.page)


class DealSpider(ABC, BasicSpider):
    name = 'deal_spider'
    website = Website.OTHER
    url_type = DealUrl
    base_url: str = ''

    def __init__(self, config: dict, keep_update=False, last_update: Optional[datetime] = None, **kwargs):
        super().__init__(**kwargs)
        self.last_update: datetime = datetime(1990, 1, 1)
        if last_update is not None:
            self.last_update = last_update
        self.searches = [search for search in config['searches'] if search['search'] is None or search['search']]
        for search in self.searches:
            for key in config['default'].keys():
                if key not in search:
                    search[key] = config['default'][key]
            search['category'] = Category.label_to_value[search['category']]
            search['search_for'] = ModelCategory.labels.index(search['search_for'])
        url_type = self.__class__.url_type
        self.deal_urls: List[url_type] = []
        self.keep_update = keep_update

    def start_requests(self):

        max_pages = 0
        for search in self.searches:
            for keyword in search['keywords']:
                max_pages += search['max_pages']
                url_type = self.__class__.url_type
                deal_url: url_type = url_type(self.base_url, search)
                self.fill_url(deal_url, search, keyword)
                self.deal_urls.append(deal_url)

        self.send_status(ScraperStatus.AMOUNT_PAGES, [max_pages])

        for deal_url in self.deal_urls:
            yield scrapy.Request(url=deal_url.url, callback=self.parse, dont_filter=True,
                                 cb_kwargs={'deal_url': deal_url})

    def parse(self, response, **kwargs):
        url_type = self.__class__.url_type
        deal_url: url_type = kwargs['deal_url']
        go_to_next_page = True
        self.send_status(ScraperStatus.MESSAGE, ['Scraping: {}/{}... ({})'.format(str(deal_url), deal_url.search['max_pages'], deal_url.url)])
        # print('Scraping: {}/{}...'.format(str(deal_url), deal_url.search['max_pages']))

        if deal_url.page >= deal_url.search['max_pages']:
            go_to_next_page = False

        locale.setlocale(locale.LC_TIME, "fr_FR")

        items = self.get_list_item(response)
        if len(items) == 0:
            print('/!\ No items found')

        for item in items:
            try:
                if not self.is_valid_item(item):
                    continue
                item_id = self.get_item_id(item)
                title, title_translated = self.get_item_titles(item)
                guessed_components, deal_type, deal_status = Guesser.guess_components(deal_url.search['search_for'], title, title_translated)
                url = self.get_item_url(item)
                thumb_url = self.get_item_thumb_url(item)
                price = self.get_item_price(item)
                shipping_price = self.get_item_shipping_price(item)
                full_price = price + shipping_price
                condition = self.get_item_condition(item)
                upload_date = self.get_item_date(item)
            except Exception as e:
                print(e)
                continue

            if not self.keep_update and self.last_update < upload_date and Deal.exists(item_id, self.website, url, deal_url.search['search_for'], self.last_update) != -1:
                self.send_status(ScraperStatus.PAGE_DONE, [])
                self.send_status(ScraperStatus.MESSAGE,
                                     ['Stumbled upon existing deal, stop: {}/{}...'.format(str(deal_url), deal_url.search['max_pages'])])
                self.send_status(ScraperStatus.PAGE_SKIP, [deal_url.search['max_pages'] - deal_url.page])
                go_to_next_page = False
                break

            yield {
                'OBJ_TYPE': Deal,
                'EXIST': Deal.exists(item_id, self.website, url, deal_url.search['search_for'], self.last_update),
                'UPDATE': False,
                'ARGS': {
                    'item_id': item_id,
                    'title': title,
                    'components': guessed_components,
                    'type': deal_type,
                    'status': deal_status,
                    'url': url,
                    'thumb_url': thumb_url,
                    'image_urls': [thumb_url],
                    'price': price,
                    'full_price': full_price,
                    'condition': condition,
                    'upload_date': upload_date,
                    'category': deal_url.search['search_for'],
                    'website': self.website
                }
            }

        self.send_status(ScraperStatus.PAGE_DONE, [])
        if go_to_next_page:
            self.send_status(ScraperStatus.MESSAGE, ['Go to next page for: {}/{}'.format(str(deal_url), deal_url.search['max_pages'])])
            # print('Go to next page for: {}/{}'.format(str(deal_url), deal_url.search['max_pages']))
            # next_page_url = response.selector.xpath("//a[@class='gspr next']/@href").get()
            deal_url.page_number(deal_url.page + 1)
            yield scrapy.Request(url=deal_url.url, callback=self.parse, dont_filter=True,
                                 cb_kwargs={'deal_url': deal_url})

    @staticmethod
    def trim_text(txt: str) -> str:
        return re.sub(r'[\r\n\t\\]', '', txt)

    @staticmethod
    def trim_price(txt: str) -> float:
        if txt.find('à') != -1:
            txt = txt[:txt.find('à') - 1]
        price = re.sub(r'[^0-9,]', '', txt).replace(',', '.')
        if price == '':
            return ReferenceValue.DEFAULT_SHIPPING_PRICE
        return float(price)

    @abstractmethod
    def get_list_item(self, response):
        return []

    @abstractmethod
    def fill_url(self, url, search, keyword):
        return url

    @abstractmethod
    def is_valid_item(self, item) -> bool:
        return False

    @abstractmethod
    def get_item_id(self, item) -> Union[str, int]:
        return 0

    @abstractmethod
    def get_item_titles(self, item) -> Tuple[str, str]:
        return '', ''

    @abstractmethod
    def get_item_url(self, item) -> str:
        return ''

    @abstractmethod
    def get_item_thumb_url(self, item) -> str:
        return ''

    @abstractmethod
    def get_item_price(self, item) -> float:
        return 1.0

    @abstractmethod
    def get_item_shipping_price(self, item) -> float:
        return 0.0

    @abstractmethod
    def get_item_condition(self, item) -> int:
        return 0

    @abstractmethod
    def get_item_date(self, item):
        return datetime.now()
