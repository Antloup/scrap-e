import datetime
import re
from typing import Optional, List, Tuple, Union

from global_vars import Website, ReferenceValue
from scrapers.deal import DealUrl, DealSpider
from global_vars.model import Condition


class ParuvenduUrl(DealUrl):
    def add_listing(self, listing: str):
        pass

    def add_conditions(self, conditions: List[int]):
        pass

    def add_keywords(self, keywords: Optional[str]):
        super().add_keywords(keywords)
        if keywords is not None:
            self.url += '&fulltext=' + keywords.replace(' ', '+')
        return self

    def add_category(self, category: int):
        pass

    def add_price(self, high: int = -1, low: int = -1):
        if high == -1 and low == -1:
            return self
        if low != -1:
            self.url += 'px0=' + str(low)
        if high != -1:
            self.url += 'px1=' + str(high)
        return self

    def page_number(self, page_num: int):
        super().page_number(page_num)
        self.remove_page('p')
        if page_num != 1:
            self.url += '&p=' + str(page_num)

    def sort_by(self, sort: int):
        pass

    def add_title_only(self):
        if self.search['title_only'] is not None and self.search['title_only']:
            self.url += '&modeFullText=titre'
        return self


class ParuvenduSpider(DealSpider):
    name = 'paruvendu'
    url_type = ParuvenduUrl
    website = Website.PARUVENDU
    website_url: str = 'https://www.paruvendu.fr/'
    base_url: str = 'https://www.paruvendu.fr/mondebarras/listefo/default/default/?elargrayon=1&ray=50&idtag=&libelle_lo=&codeinsee=&lo=&pa=&ray=50&r=&px1=&zmd[]=VENTE&zmd[]=TROC&zmd[]=DON&zmd[]=RECH&px0=&codPro=&filtre=&tri='

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_delay = 24.42

    def get_list_item(self, response):
        return list(response.selector.xpath("//form[@id='rechercher']/div[@class='v2-contenthome flol']/div[@class='debarras-annonce']"))


    def fill_url(self, url, search, keyword):
        url.add_price(search['max_price'], search['min_price'])\
           .add_keywords(keyword)\
           .add_title_only()

    def is_valid_item(self, item) -> bool:
        if str(item.xpath(".//div[@class='debarras-priceannonce']/text()").get()).lower().replace('\r\n','') == 'faire offre':
            return False
        return True

    def get_item_id(self, item) -> Union[str, int]:
        return item.xpath("./div/@data-id").get()

    def get_item_titles(self, item) -> Tuple[str, str]:
        return item.xpath(".//a//h3/text()").get(), ''

    def get_item_url(self, item) -> str:
        return item.xpath(".//a[@class='globann']/@href").get()

    def get_item_thumb_url(self, item) -> str:
        return item.xpath(".//a//img/@src").get()

    def get_item_price(self, item) -> float:
        try:
            ret = float(item.xpath(".//div[@class='debarras-priceannonce']/text()").get().replace('€','').replace('\r\n','').replace(' ',''))
        except:
            ret = None
        return ret


    def get_item_shipping_price(self, item) -> float:
        return ReferenceValue.PARUVENDU_SHIPPING_PRICE

    def get_item_condition(self, item) -> int:
        return Condition.USED

    def get_item_date(self, item):
        return datetime.datetime.now()  # TODO
