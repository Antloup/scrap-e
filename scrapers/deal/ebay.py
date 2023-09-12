import re
from typing import List, Optional, Dict, Callable, Union, Tuple

from global_vars.ebay import Listing, Category, ShippingType, UrlCondition, UrlListing, UrlSort, Condition as DealCondition
from global_vars.model import Website, Category as ModelCategory, Condition as ModelCondition, ReferenceValue, \
    date_format
from datetime import date, datetime
from scrapers.deal.deal_spider import DealSpider, DealUrl


class EbayUrl(DealUrl):
    def __init__(self, url: str, search: dict, page: int = 1):
        super().__init__(url, search, page)

    def sort_by(self, sort: int):
        self.url += '&_sop=' + str(sort)
        return self

    def add_listing(self, listing: str):
        self.url += '&LH_' + listing + '=1'
        return self

    def add_conditions(self, conditions: List[int]):
        self.url += '&LH_ItemCondition=' + ('|'.join(str(x) for x in conditions))
        return self

    def add_keywords(self, keywords: Optional[str]):
        super().add_keywords(keywords)
        if keywords is not None:
            # self.keywords = keywords
            self.url += '&_nkw=' + keywords.replace(' ','+')
        return self

    def add_category(self, category: int):
        self.url += '&_sacat=' + str(category)
        return self

    def add_price(self, high: int = -1, low: int = -1):
        if high > 0:
            self.url += '&_udhi=' + str(high)
        if low > 0:
            self.url += '&_udlo=' + str(low)
        return self

    def page_number(self, page_num: int):
        super().page_number(page_num)
        self.remove_page('_pgn')
        if page_num != 1:
            self.url += '&_pgn=' + str(page_num)
        # if re.search(r'&_pgn=[\w]+(&|$)', self.url) is None:
        #     if page_num != 1:
        #         self.url += '&_pgn=' + str(page_num)
        # else:
        #     if page_num != 1:
        #         self.url = re.sub(r'&_pgn=[\w]+(&|$)', '&_pgn=' + str(page_num), self.url)
        #     else:
        #         self.url = re.sub(r'&_pgn=[\w]+(&|$)', '', self.url)
        return self

    def __str__(self):
        return 'category {} | keywords {} | page {}'\
            .format(ModelCategory.labels[Category.convert(self.category)], self.keywords if self.keywords != '' else 'ALL', self.page)


class EbaySpider(DealSpider):
    name = 'ebay'
    title_prefix = 'Cliquez sur ce lien pour l\'afficher '
    url_type = EbayUrl
    website = Website.EBAY
    base_url: str = 'https://www.ebay.fr/sch/i.html?_from=R40&_ipg=200&rt=nc&LH_PrefLoc=3'  # 200 results per page, item from region, in european union

    def fill_url(self, url: EbayUrl, search, keyword):
        # TODO: (Bid url)
        url.add_listing(UrlListing.AUCTION_AND_FIXED) \
            .add_conditions([UrlCondition.NEW_OTHER, UrlCondition.MAN_REFURB, UrlCondition.SELLER_REFURB, UrlCondition.USED, UrlCondition.NOT_WORKING]) \
            .add_price(search['max_price'], search['min_price']) \
            .add_keywords(keyword) \
            .sort_by(UrlSort.NEW)

    def get_list_item(self, response):
        return list(response.selector.xpath("body//div[@id='srp-river-results']/ul/li"))

    def is_valid_item(self, item) -> bool:
        if item.xpath(".//h3/parent::a/@href").get() is None:
            return False
        return True

    def get_item_id(self, item) -> Union[str, int]:
        item_id = self.trim_text(item.xpath(".//h3/parent::a/@href").get())
        item_id = int(re.search(r"itm/.*?/([0-9]+)\?", item_id).group(1))
        return item_id

    def get_item_titles(self, item) -> Tuple[str, str]:
        title_translated = ''
        title = item.xpath(".//h3/text()").get()
        if title is None:
            title = item.xpath(".//h3/span/text()").get()
        # title_translated = item.xpath(".//h3/parent::a/@title").get()[len(self.title_prefix):]  # Translated title
        # title = item.xpath(".//h3/parent::a/@data-mtdes").get()  # Original title
        # if title is None or title == '':
        #     title = title_translated
        return title, title_translated

    def get_item_url(self, item) -> str:
        return item.xpath(".//h3/parent::a/@href").get()

    def get_item_thumb_url(self, item) -> str:
        return item.xpath(".//img/@src").get()

    def get_item_price(self, item) -> float:
        price = item.xpath(".//span[@class='s-item__price']/text()").get()
        if price is None:
            price = item.xpath(".//span[@class='s-item__price']/span/text()").get()
        price = self.trim_text(price)
        # price = self.trim_text(item.xpath(".//li[@class='lvprice prc']/span/text()").get())
        if price == '':  # Text got boundaries like '20 EUR à 50 EUR'
            price = self.trim_text(item.xpath(".//li[@class='lvprice prc']/span/span/text()").get())
        price = self.trim_price(price)
        return price

    def get_item_shipping_price(self, item) -> float:
        if item.xpath(".//span[@class='s-item__shipping s-item__logisticsCost']/text()").get() == 'Livraison gratuite':
        # if item.xpath(".//li[@class='lvshipping']/span/span/span/text()").get() == 'Livraison gratuite':
            shipping_price = 0.0
        else:
            shipping_price = item.xpath(".//span[@class='s-item__shipping s-item__logisticsCost']/text()").get()
            if shipping_price is not None:
                shipping_price = self.trim_price(shipping_price)
            else:
                shipping_price = ReferenceValue.DEFAULT_SHIPPING_PRICE

        return shipping_price

    def get_item_condition(self, item) -> int:
        condition = item.xpath(".//div[@class='s-item__subtitle']/span/text()").get()
        # condition = item.xpath(".//div[@class='lvsubtitle']/text()").get()
        if condition is not None:
            condition = self.trim_text(condition)
            condition = DealCondition.convert(condition)
        else:
            condition = ModelCondition.OTHER

        return condition

    def get_item_date(self, item):
        today = date.today()
        date_text = item.xpath(".//span[@class='s-item__dynamic s-item__listingDate']/span/text()").get() + ' ' + str(today.year)
        # date_text = item.xpath(".//span[@class='tme']/span/text()").get() + ' ' + str(today.year)
        date_text = date_text.replace('janv.','janvier')
        date_text = date_text.replace('févr.','février')
        date_text = date_text.replace('avr.','avril')
        date_text = date_text.replace('juil.','juillet')
        date_text = date_text.replace('sept.','septembre')
        date_text = date_text.replace('oct.','octobre')
        date_text = date_text.replace('nov.','novembre')
        date_text = date_text.replace('déc.','décembre')
        date_object = datetime.strptime(date_text, date_format)

        return date_object
