import datetime
import re
from typing import Optional, List, Tuple, Union

from global_vars import Website, ReferenceValue
from scrapers.deal import DealUrl, DealSpider
from global_vars.model import Condition


class LbcUrl(DealUrl):
    def add_listing(self, listing: str):
        pass

    def add_conditions(self, conditions: List[int]):
        pass

    def add_keywords(self, keywords: Optional[str]):
        super().add_keywords(keywords)
        if keywords is not None:
            self.url += '&text=' + keywords.replace(' ', '+')
        return self

    def add_category(self, category: int):
        pass

    def add_price(self, high: int = -1, low: int = -1):
        if high == -1 and low == -1:
            return self
        high = 'max' if high == -1 else str(high)
        low = 'min' if low == -1 else str(low)
        self.url += '&price=' + str(low) + '-' + str(high)
        return self

    def page_number(self, page_num: int):
        super().page_number(page_num)
        self.remove_page('page')
        if page_num != 1:
            self.url += '&page=' + str(page_num)

    def sort_by(self, sort: int):
        pass

    def add_title_only(self):
        if self.search['title_only'] is not None and self.search['title_only']:
            self.url += '&search_in=subject'
        return self


class LbcSpider(DealSpider):
    name = 'lbc'
    url_type = LbcUrl
    website = Website.LE_BON_COIN
    website_url: str = 'https://www.leboncoin.fr'
    base_url: str = 'https://www.leboncoin.fr/recherche/?category=15&shippable=1&locations=d_1'  # Shippable + IT category + Ain

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_delay = 24.42

    def get_list_item(self, response):
        return list(response.selector.xpath("//div[@class='_2r1q3']//ul/li"))
        # return list(response.selector.xpath("//div[@data-reactid='364']/ul/li"))

    def fill_url(self, url, search, keyword):
        url.add_price(search['max_price'], search['min_price'])\
           .add_keywords(keyword)\
           .add_title_only()

    def is_valid_item(self, item) -> bool:
        if item.xpath("@class").get() is None:
        # if item.xpath("a//div[@data-test-id='deliveryOption']").get() is None or item.xpath("@class").get() is None:
            return False
        return True

    def get_item_id(self, item) -> Union[str, int]:
        return int(re.search(r'\/([0-9]+)\.htm',item.xpath("a/@href").get()).group(1))

    def get_item_titles(self, item) -> Tuple[str, str]:
        return item.xpath("a//span[@itemprop='name']/text()").get(), ''

    def get_item_url(self, item) -> str:
        return self.website_url + item.xpath("a/@href").get()

    def get_item_thumb_url(self, item) -> str:
        return ''
        # return item.xpath("//a//img/@src").get()  # Image is ajax

    def get_item_price(self, item) -> float:
        return float(item.xpath("a//span[@itemprop='priceCurrency']/text()").get())

    def get_item_shipping_price(self, item) -> float:
        return ReferenceValue.LBC_SHIPPING_PRICE

    def get_item_condition(self, item) -> int:
        return Condition.USED

    def get_item_date(self, item):
        return datetime.datetime.now()  # TODO
