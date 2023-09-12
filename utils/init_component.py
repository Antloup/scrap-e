from global_vars.model import Condition, DdrType, Category, MotherboardType, CaseType, OsType, PlayerType
from models import Component, Deal, DealComponent, ComponentCpu, ComponentGpu
from scrapers import ScraperPool
from scrapers.component import BenchmarkSpider, UserBenchmarkSpider


def init_cpu_gpu_component():
    print('Scrap benchmark.net : creating component + basic perf...')
    scraper = ScraperPool([BenchmarkSpider], blocking_start=True)
    scraper.start()
    print('Done !')

    # Update performance
    print('Scrap benchmark.net : update performance...')
    scraper = ScraperPool([UserBenchmarkSpider], blocking_start=True)
    scraper.start()
    print('Done !')


def init_ram_component():
    ram_size_list = [i for i in range(1, 33)] + [0.128, 0.256, 0.512]
    ram_speed_list = {DdrType.DDR1: [200, 266, 300, 333, 400, 433, 466, 500, 533, 538, 550, 600],
                      DdrType.DDR2: [400, 533, 667, 800, 1066],
                      DdrType.DDR3: [800, 1066, 1333, 1600, 1866, 2133],
                      DdrType.DDR4: [1600, 1866, 2133, 2400, 2666, 2933, 3200]}
    ram_type_list = [DdrType.DDR1, DdrType.DDR2, DdrType.DDR3, DdrType.DDR4]

    for ram_size in ram_size_list:
        for ram_type in ram_type_list:
            for ram_speed in ram_speed_list[ram_type]:
                if ram_size < 1.0:
                    name_size = str(1000 * ram_size) + ' Mo'
                else:
                    name_size = str(ram_size) + ' Go'
                name_type = DdrType.labels[ram_type]
                name_speed = str(ram_speed) + ' Mhz'
                name = ' '.join([name_size, name_type, name_speed])
                Component.create(name=name, category=Category.RAM, amount=ram_size, speed=ram_speed, ddr=ram_type)


def init_drive_component():
    amount_list = [32, 64, 80, 90, 100, 120, 128, 240, 250, 256, 280, 320, 400, 480, 500, 512, 600, 640, 680, 700, 720, 750,
                   800, 900, 960, 970, 1000, 1290, 1920, 2000, 3000, 3840, 4000, 6000, 8000, 10000, 12000, 14000, 16000]
    for amount in amount_list:
        if amount >= 1000:
            if amount/1000 % 1 == 0:
                name = str(int(amount/1000)) + ' To'
            else:
                name = str(round(float(amount)/1000.0, 2)) + ' To'
        else:
            name = str(amount) + ' Go'
        Component.create(category=Category.HDD, name=name, amount=amount)
        Component.create(category=Category.SSD, name=name, amount=amount)


def init_psu_component():
    amount_list = [120, 160, 200, 250, 300, 350, 400, 430, 450, 500, 520, 550, 600, 620, 650, 700, 750, 800, 850, 900,
                   950, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 2000]
    for amount in amount_list:
        name = str(amount) + 'W'
        Component.create(category=Category.PSU, name=name, amount=amount)


def init_case_component():
    for i, case in enumerate(CaseType.labels):
        Component.create(category=Category.CASE, name=case, case_type=i)


def init_mb_component():
    for i, mb in enumerate(MotherboardType.labels):
        Component.create(category=Category.MB, name=mb, mb_type=i)


def init_os_component():
    for i, os in enumerate(OsType.labels):
        Component.create(category=Category.OS, name=os, os=i)


def init_player_component():
    for i, player in enumerate(PlayerType.labels):
        Component.create(category=Category.PLAYER, name=player, player_type=i)


def init_predefined_component():
    init_ram_component()
    init_drive_component()
    init_psu_component()
    init_case_component()
    init_mb_component()
    init_os_component()
    init_player_component()
