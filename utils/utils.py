import re

from global_vars.ebay import EbayId, Category as EbayCategory
from global_vars.model import Condition, DdrType, Category, MotherboardType, CaseType, OsType, PlayerType
from ebaysdk.trading import Connection as TradingConnection

from models import Component, Deal, DealComponent, ComponentCpu, ComponentGpu

def show_filtered():

    print('--- Filtered Data ---')
    value_rate: float = 0.5
    min_cpu_perf = Component.get(Component.name == 'Intel Core i5 2400').benchmark_net_score
    min_gpu_perf = Component.get(Component.name == 'GeForce GTX 1050').benchmark_net_score
    # min_gpu_perf = Component.get(Component.name == 'Radeon HD 4850').benchmark_net_score

    for deal in Deal.select().join(DealComponent).join(Component).join(ComponentCpu)\
                             .where((ComponentCpu.benchmark_net_score >= min_cpu_perf) & (~Component.name.contains('xeon') & (Deal.benchmark_net_value >= value_rate) & (Deal.condition != Condition.NOT_WORKING)))\
                             .order_by(Deal.benchmark_net_value.desc()):
        deal.print()
    for deal in Deal.select().join(DealComponent).join(Component).join(ComponentGpu) \
                             .where((ComponentGpu.benchmark_net_score >= min_gpu_perf) & (Deal.benchmark_net_value >= value_rate) & (Deal.condition != Condition.NOT_WORKING))\
                             .order_by(Deal.benchmark_net_value.desc()):
        deal.print()


def get_categories():
    api = TradingConnection()

    callData = {
        'DetailLevel': 'ReturnAll',
        'CategorySiteID': EbayId.FRANCE_ID,
        'CategoryParent': EbayCategory.COMPONENT,
        'LevelLimit': 3,
    }

    response = api.execute('GetCategories', callData)

    for item in response.reply.CategoryArray.Category:
        print(item.CategoryName + ' ' + item.CategoryID)


def print_clock_duplicates():
    mylist = []
    for comp in Component.select().where(Component.name.contains(' @ ')):
        print(comp.name)
        mylist.append(re.sub(r' @ .*$', '', comp.name))
    print('size:{}'.format(len(mylist)))
    print('duplicates:')
    for y in set([x for x in mylist if mylist.count(x) > 1]):
        print(y)
    mylist = list(dict.fromkeys(mylist))
    print('size without clock speed:{}'.format(len(mylist)))
