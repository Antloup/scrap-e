from dataclasses import dataclass


@dataclass
class ReferenceValue:
    DEFAULT_SHIPPING_PRICE = 15.0
    LBC_SHIPPING_PRICE = 7.0 + 4.80  # Shipping + "Protection leboncoin"
    PARUVENDU_SHIPPING_PRICE = 8.0

    BENEFIT_VALUE = 1.0
    GPU_FACTOR = 0.65  # GPU Second Hand factor
    CPU_FACTOR = 0.6  # CPU Second Hand factor

    # Price / performance
    CPU_BENCHMARK_NET = (96 / 6841.0 + 240 / 10928.0 + 148 / 12928.0) / 3  # Core i3-9100F, Core i5-9600KF, Ryzen 3 3300X
    GPU_BENCHMARK_NET = (200 / 8724.0 + 400 / 16730.0 + 220 / 9890.0) / 3  # RX 580, RX 5700-XT,  GTX 1650S (Super)
    CPU_USERBENCHMARK = (96 / 82.1 + 240 / 95.0 + 148 / 83.0) / 3  # Core i3-9100F, Core i5-9600KF, Ryzen 3 3300X
    GPU_USERBENCHMARK = (200 / 57.0 + 400 / 107.0 + 220 / 58.5) / 3  # RX 580, RX 5700-XT,  GTX 1650S (Super)
    HDD = 0.05  # Price/Go
    SSD = 0.10  # Price/Go
    RAM = [1, 0.8, 2, 4, 5]  # Price/Go [OTHER, DDR1, DDR2, DDR3, DDR4]
    PSU = 0.05  # Price/Watt
    CASE = 15  # Base price
    # ['OTHER', 'OLD_SLIM', 'OLD_LARGE', 'OLD_GAMING', 'NEW_SLIM', 'NEW_LARGE', 'NEW_GAMING']
    CASE_FACTOR = [1.0, 0.6, 0.9, 1.3, 1.0, 1.4, 1.9]
    MB = 35  # Base price
    # ['OTHER', 'OLD', 'NEW', 'GAMING']
    MB_FACTOR = [1.0, 0.5, 1.0, 1.8]
    OS = 10
    # ['OTHER', 'Windows < XP', 'Windows XP', 'Windows VISTA', 'Windows 7 Home', 'Windows 7 Pro',
    # 'Windows 8 Home', 'Windows 8 Pro', 'Windows 10 Home', 'Windows 10 Pro', 'Linux', 'No OS']
    OS_FACTOR = [0, 0, 0, 0, 0.4, 0.6, 0.5, 0.7, 1.0, 1.2, 0, 0]
    PLAYER = 10
    # ['OTHER', 'CD', 'DVD', 'DVD-RW', 'Blu Ray']
    PLAYER_FACTOR = [1.0, 0, 1.0, 1.2, 7.0]


@dataclass
class Category:
    labels = []
    OTHER: int = 0
    CPU: int = 1
    GPU: int = 2
    RAM: int = 3
    MB: int = 4
    HDD: int = 5
    SSD: int = 6
    CASE: int = 7
    PSU: int = 8
    OS: int = 9
    PLAYER: int = 10


@dataclass
class DealType:
    labels = []
    UNK: int = 0
    SINGLE_ITEM: int = 1
    MULTIPLE_ITEM: int = 2
    LOT: int = 3
    USELESS: int = 4


@dataclass
class DealStatus:
    labels = []
    UNK: int = 0
    SURE: int = 1
    MIXED: int = 2


@dataclass
class DealClass:
    labels = []
    UNDEF: int = 0
    UNK: int = 1
    REAL: int = 2
    FAKE: int = 3


@dataclass
class Listing:
    labels = []
    UNK = 0
    AUCTION = 1
    AUCTION_AND_FIXED = 2
    CLASSIFIED = 3
    FIXED = 4
    STORE_INV = 5


@dataclass
class Website:
    labels = []
    OTHER = 0
    EBAY = 1
    LE_BON_COIN = 2
    PARUVENDU = 3


@dataclass
class Condition:
    labels = []
    OTHER = 0
    NEW = 1
    REFURB = 2
    USED = 3
    NOT_WORKING = 4


@dataclass
class DdrType:
    labels = []
    OTHER = 0
    DDR1 = 1
    DDR2 = 2
    DDR3 = 3
    DDR4 = 4


@dataclass
class CaseType:
    labels = []
    OTHER = 0
    OLD_SLIM = 1
    OLD_LARGE = 2
    OLD_GAMING = 3
    NEW_SLIM = 4
    NEW_LARGE = 5
    NEW_GAMING = 6


@dataclass
class MotherboardType:
    labels = []
    OTHER = 0
    OLD = 1
    NEW = 2
    GAMING = 3


@dataclass
class OsType:
    labels = []
    OTHER = 0
    W_OLD = 1
    W_XP = 2
    W_VISTA = 3
    W_7_HOME = 4
    W_7_PRO = 5
    W_8_HOME = 6
    W_8_PRO = 7
    W_10_HOME = 8
    W_10_PRO = 9
    LINUX = 10
    NO_OS = 11


@dataclass
class PlayerType:
    labels = []
    OTHER = 0
    CD = 1
    DVD = 2
    DVD_RW = 3
    BLU_RAY = 4

date_format = '%B-%d %H:%M %Y'


for class_type in [Category, DealType, DealStatus, Listing, Website, Condition, DdrType, CaseType, MotherboardType, OsType, PlayerType]:
    class_type.labels = [key.replace('_',' ') for key, value in vars(class_type).items() if not key.startswith('__') and key.upper() == key]
