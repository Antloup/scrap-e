# Infos on Ebay:
# Lot mixtes category : doesn't really worth it
# Important link :
# - Category list: https://pages.ebay.com/sellerinformation/news/categorychanges.html
from dataclasses import dataclass
from global_vars.model import Listing as ModelListing, Category as ModelCategory, Condition as ModelCondition


@dataclass
class EbayId:
    FRANCE_ID = 71
    FRANCE_GLOBAL_ID = 'EBAY-FR'


@dataclass
class Category:
    label_to_value = {}
    COMPUTER: int = 58058
    PC: int = 179
    COMPONENT: int = 175673
    ACCESSORIES: int = 31530
    OTHER: int = 162
    COMPONENT_OTHER: int = 16145
    COMPONENT_FAN: int = 42000
    VIDEO_GAMES: int = 1249

    CPU = 164
    GPU = 27386
    RAM = 170083
    MB = 1244
    MB_WITH_CPU = 131511
    MB_COMPONENT = 182090
    PSU = 42017
    SC = 44980

    convert_dict = dict({CPU: ModelCategory.CPU,
                         GPU: ModelCategory.GPU})

    @classmethod
    def convert(cls, category: int) -> int:
        if category not in cls.convert_dict:
            return ModelCategory.OTHER
        return cls.convert_dict[category]


Category.label_to_value = {key: value for key, value in vars(Category).items() if not key.startswith('__') and key.upper() == key}


@dataclass
class UrlCondition:
    NEW = 1000
    NEW_OTHER = 1500
    NEW_WITH_DEFECTS = 1750
    MAN_REFURB = 2000
    SELLER_REFURB = 2500
    USED = 3000
    VGOOD = 4000
    GOOD = 5000
    ACCEPT = 6000
    NOT_WORKING = 7000


@dataclass
class UrlListing:
    AUCTION = 'Auction'
    AUCTION_AND_FIXED = 'BIN'

@dataclass
class UrlSort:
    NEW = 10


@dataclass
class Listing:
    AUCTION = 'Auction'
    AUCTION_AND_FIXED = 'AuctionWithBIN'
    CLASSIFIED = 'Classified'
    FIXED = 'FixedPrice'
    STORE_INV = 'StoreInventory'

    convert_dict = dict({AUCTION: ModelListing.AUCTION,
                         AUCTION_AND_FIXED: ModelListing.AUCTION_AND_FIXED,
                         CLASSIFIED: ModelListing.CLASSIFIED,
                         FIXED: ModelListing.FIXED,
                         STORE_INV: ModelListing.STORE_INV})

    @classmethod
    def convert(cls, category: str) -> int:
        if category not in cls.convert_dict:
            return ModelCondition.OTHER
        return cls.convert_dict[category]


@dataclass
class ShippingType:
    NOT_SPECIFIED = 'NotSpecified'


@dataclass
class Condition:
    convert_dict = dict({'D\'occasion': ModelCondition.USED,
                         'Reconditionné': ModelCondition.REFURB,
                         'Neuf': ModelCondition.NEW,
                         'Neuf (autre)': ModelCondition.NEW,
                         'Pièces détachées uniquement': ModelCondition.NOT_WORKING,
                         'Ouvert (jamais utilisé)': ModelCondition.REFURB})

    @classmethod
    def convert(cls, category: str) -> int:
        if category not in cls.convert_dict:
            return ModelCondition.OTHER
        return cls.convert_dict[category]
