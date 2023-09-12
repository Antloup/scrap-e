import re
from typing import List
from peewee import fn

from global_vars import CaseType, MotherboardType, PlayerType, OsType
from models import Component, Category, DealType, DealStatus


class Guesser:

    nogo_list: List = ['box.+only', 'only.+box', 'only.+housing', 'housing.+only', 'boite.+vide', 'sans.?carte', 'boite.?seul', 'uniquement',
                 'seulement', 'vintage', 'raffle', 'packaging.+only', 'lüfter(satz)?']

    nogo_list_cat = {Category.GPU: ['air.+cooler', 'cooler.+only', 'solo.+cooler', 'no.+gpu', 'no.+card', 'cooler.+fan',
                          'cooling.+fan', 'heatsink.+only', 'bridge', 'cable', 'back.*plate', 'waterblocks?', 'radiateur', 'heatsink',
                          '(32|64|128|256|512)[^0-9]?m(b|o)', 'fan for', 'ventilateur', 'refroidissement'],
                     Category.CPU: []}

    keywords_list = {Category.GPU: ['quadro', 'radeon', 'vega', 'rtx', 'gtx', 'rx', 'ti', 'xt', 'titan', 'hd', 'r5', 'r7', 'r9', 'rx', 'super'],
                     Category.CPU: ['amd', 'intel', 'pentium', 'celeron', 'athlon', 'threadripper', 'xeon', 'core2',
                                    'duo', 'core', 'quad', 'gold', 'silver', 'bronze', 'fx', 'opteron', 'phenom', 'i3',
                                    'i5', 'i7', 'i9', 'ryzen 3', 'ryzen 5', 'ryzen 7', 'ryzen 9', 'ryzen'],
                     Category.PLAYER: { PlayerType.labels[PlayerType.DVD]: 'dvd',
                                        PlayerType.labels[PlayerType.CD]: 'cd',
                                        PlayerType.labels[PlayerType.BLU_RAY]: 'blu.?ray'},
                     Category.OS: {OsType.labels[OsType.W_XP]: 'w(in)?(dows)?\s?xp',
                                   OsType.labels[OsType.W_VISTA]: 'w(in)?(dows)?\s?vista',
                                   OsType.labels[OsType.W_7_PRO]: 'w(in)?(dows)?\s?(7|seven)\s?pro(fessional)?\s?(32|64)?',
                                   OsType.labels[OsType.W_7_HOME]: 'w(in)?(dows)?\s?(7|seven)\s?(32|64)?',
                                   OsType.labels[OsType.W_8_PRO]: 'w(in)?(dows)?\s?(8|eight)\s?pro(fessional)?\s?(32|64)?',
                                   OsType.labels[OsType.W_8_HOME]: 'w(in)?(dows)?\s?(8|eight)\s?(32|64)?',
                                   OsType.labels[OsType.W_10_PRO]: 'w(in)?(dows)?\s?(10|ten)\s?pro(fessional)?\s?(32|64)?',
                                   OsType.labels[OsType.W_10_HOME]: 'w(in)?(dows)?\s?(10|ten)\s?(32|64)?'}}

    expr_base = "(^|\s){}($|\s)"

    @classmethod
    def guess_components(cls, category: int, deal_title: str, deal_title_translated: str = '') -> (List[Component], int, int):
        deal_title = cls.trim(deal_title)
        deal_title_translated = cls.trim(deal_title_translated)

        if re.search(cls.expr_base.format('lot'), deal_title) is not None or re.search(cls.expr_base.format('lot'), deal_title_translated) is not None:
            # TODO: (handle Lot / Set / Batch)
            return [], DealType.LOT, DealStatus.SURE

        if category == Category.OTHER:
            return cls.guess_multiple_components(category, deal_title, deal_title_translated)
        else:
            return cls.guess_single_components(category, deal_title, deal_title_translated)

    @classmethod
    def guess_single_components(cls, category: int, deal_title: str, deal_title_translated: str = '',
                                skip_nogo: bool = False) -> (List[Component], int, int):

        if not skip_nogo:
            nogo_list = ['(' + cls.expr_base.format(x) + ')' for x in cls.nogo_list + cls.nogo_list_cat[category]]
            nogo_expr = r'(' + '|'.join(nogo_list) + ')'

            if re.search(nogo_expr, deal_title) is not None or\
                    re.search(nogo_expr, deal_title_translated) is not None or\
                    (re.search(cls.expr_base.format('[0-9.,]+\s*a'), deal_title) and re.search(cls.expr_base.format('[0-9.,]+\s*v'), deal_title)) is not None or\
                    (re.search(cls.expr_base.format('[0-9.,]+\s*w'), deal_title) and re.search(cls.expr_base.format('(adapter|ac|oem)'), deal_title)) is not None:  # Might be power supply
                return [], DealType.USELESS, DealStatus.SURE

        prev_query = Component.select()

        words = deal_title.split()

        # Split Letter-Number-Letter component
        for word in words:
            if re.search(r"^([^0-9]+)([0-9].*)", word) is not None:
                words.append(re.search(r"^([^0-9]+)([0-9].*)", word).group(1))
                words.append(re.search(r"^([^0-9]+)([0-9].*)", word).group(2))
            if re.search(r"([0-9]+)([^0-9]+)$", word) is not None:
                words.append(re.search(r"([0-9]+)([^0-9]+)$", word).group(1))
                words.append(re.search(r"([0-9]+)([^0-9]+)$", word).group(2))

        has_any_keyword = False

        # Pre-filter with keywords list
        for keyword in cls.keywords_list[category]:
            if keyword not in words:
                continue
            has_any_keyword = True
            deal_title = deal_title.replace(keyword, '')
            query = prev_query.where((Component.category == category) &
                                     ((fn.Lower(Component.name).startswith(keyword + ' ')) |
                                      (fn.Lower(Component.name).endswith(' ' + keyword)) |
                                      (fn.Lower(Component.name).contains(' ' + keyword + ' '))))
            if len(list(query)) == 1:
                return [list(query)[0]], DealType.SINGLE_ITEM, DealStatus.SURE
            elif len(list(query)) > 1:
                prev_query = query

        if not has_any_keyword:
            return [], DealType.UNK, DealStatus.UNK

        word_kept = []
        likelihood: dict = dict()
        only_empty_queries: bool = True
        for word in words:
            if not re.search(r'[a-zA-Z]*[0-9]+[a-zA-Z]*', word) or word in cls.keywords_list[category]:
                continue

            word_kept.append(word)

            query = prev_query.where((Component.category == category) &
                                     ((fn.Lower(Component.name).startswith(word + ' ')) |
                                      (fn.Lower(Component.name).endswith(' ' + word)) |
                                      (fn.Lower(Component.name).contains(' ' + word + ' '))))
            for r in list(query):
                if r in likelihood:
                    likelihood[r] += 1
                else:
                    likelihood[r] = 1

            if len(list(query)) == 1:
                return [list(query)[0]], DealType.SINGLE_ITEM, DealStatus.SURE
            elif len(list(query)) > 1:
                prev_query = query
                only_empty_queries = False

        if only_empty_queries:
            return [], DealType.UNK, DealStatus.UNK

        query_list = list(prev_query)

        if len(query_list) == 0:
            mx = max(likelihood.values())
            query_list = [k for k, v in likelihood.items() if v == mx]

        if len(query_list) > 1:
            for item in query_list:
                item.tmp = item.name.lower().replace(' ', '')
                for word in word_kept:
                    item.tmp = item.tmp.replace(word, '')
            return [min(query_list, key=lambda x: len(x.name))], DealType.SINGLE_ITEM, DealStatus.MIXED

        return [], DealType.UNK, DealStatus.UNK

    @classmethod
    def guess_multiple_components(cls, category: int, deal_title: str, deal_title_translated: str = '') -> (List[Component], int, int):
        component_list: List[Component] = []
        for cat in [Category.GPU, Category.CPU]:
            comp, _, _ = cls.guess_single_components(cat, deal_title, deal_title_translated, skip_nogo=True)
            component_list += comp

        gb_searches = [x for x in re.finditer('([0-9]+)\s?[tg][bo]', deal_title)]
        hdd_seen: bool = False
        ssd_seen: bool = False
        for gb_search in gb_searches:
            if 't' not in gb_search.group(0) and float(gb_search.group(1)) <= 32:

                ram_size = gb_search.group(1)

                ddr_search = re.search(cls.expr_base.format('ddr\s?(1|2|3|4)'), deal_title)
                if ddr_search is not None:
                    ram_type = ddr_search.group(0).replace(' ', '')
                else:
                    ram_type = 'ddr3'

                mhz_search = re.search(cls.expr_base.format('([0-9]+)\s?mhz'), deal_title)
                if mhz_search is not None:
                    ram_speed = mhz_search.group(1)
                else:
                    if ram_type == 'ddr1':
                        ram_speed = '400'
                    elif ram_type == 'ddr2':
                        ram_speed = '533'
                    elif ram_type == 'ddr3':
                        ram_speed = '1066'
                    else:
                        ram_speed = '1866'

                ram_name = ram_size + ' Go ' + ram_type + ' ' + ram_speed + ' Mhz'
                component_list.append(Component.get((fn.Lower(Component.name).contains(ram_name)) & (Component.category == Category.RAM)))
            else:
                storage_size = cls.storage_str(float(gb_search.group(1)))
                if re.search(cls.expr_base.format('((hdd.+ssd)|(ssd.+hdd))'), deal_title) is not None and not hdd_seen and not ssd_seen:
                    sizes = sorted([float(x.group(1)) for x in gb_searches if 't' not in x.group(0) and float(x.group(1)) > 32])
                    sizes += sorted([float(x.group(1)) for x in gb_searches if 't' in x.group(0)])
                    hdd_size = cls.storage_str(sizes[1]) if len(sizes) > 1 else cls.storage_str(sizes[0])
                    ssd_size = cls.storage_str(sizes[0])
                    component_list.append(Component.get((fn.Lower(Component.name).startswith(hdd_size + ' ')) & (Component.category == Category.HDD)))
                    component_list.append(Component.get((fn.Lower(Component.name).startswith(ssd_size + ' ')) & (Component.category == Category.SSD)))
                    hdd_seen = ssd_seen = True
                elif re.search(cls.expr_base.format('hdd'), deal_title) is not None and not hdd_seen:
                    component_list.append(Component.get((fn.Lower(Component.name).startswith(storage_size + ' ')) & (Component.category == Category.HDD)))
                    hdd_seen = True
                elif re.search(cls.expr_base.format('ssd'), deal_title) is not None and not ssd_seen:
                    component_list.append(Component.get((fn.Lower(Component.name).startswith(storage_size + ' ')) & (Component.category == Category.SSD)))
                    ssd_seen = True
                elif not hdd_seen:
                    component_list.append(Component.get((fn.Lower(Component.name).startswith(storage_size + ' ')) & ( Component.category == Category.HDD)))

        psu_search = re.search(cls.expr_base.format('([0-9])+\sW(att)?'), deal_title)
        if psu_search is not None:
            component_list.append(Component.get((Component.name == psu_search.group(1)) & (Component.category == Category.PSU)))
        else:
            if re.search(r'(gaming|gamer)', deal_title) is not None:
                component_list.append(Component.get((Component.name == '450W') & (Component.category == Category.PSU)))
            else:
                component_list.append(Component.get((Component.name == '300W') & (Component.category == Category.PSU)))
        for key, values in cls.keywords_list.items():
            if key not in [Category.OS, Category.PLAYER]:
                continue
            # 'w(in)?(dows)?\s?([0-9]+|xp|vista)\s?(pro|home)?'
            for k, v in values.items():
                misc_searches = re.search(cls.expr_base.format('(' + v + ')'), deal_title)
                if misc_searches is not None:
                    component_list.append(Component.get((Component.category == key) & (Component.name == k)))
                    break

        if re.search(r'(gaming|gamer)',deal_title) is not None:
            component_list.append(Component.get((Component.name == CaseType.labels[CaseType.OLD_GAMING]) & (Component.category == Category.CASE)))
            component_list.append(Component.get((Component.name == MotherboardType.labels[MotherboardType.NEW]) & (Component.category == Category.MB)))
        else:
            component_list.append(Component.get((Component.name == CaseType.labels[CaseType.OLD_LARGE]) & (Component.category == Category.CASE)))
            component_list.append(Component.get((Component.name == MotherboardType.labels[MotherboardType.OLD]) & (Component.category == Category.MB)))

        component_list = list(filter(lambda x: x is not None, component_list))

        return component_list, DealType.MULTIPLE_ITEM, DealStatus.MIXED

    @staticmethod
    def trim(s: str) -> str:
        s = re.sub(r'\W+', ' ', s.lower())  # Trim
        s = s.replace('  ', ' ')
        s = s.replace('core 2', 'core2')  # Official name
        s = s.replace('dualcore', 'dual core')  # Official name
        s = s.replace('quadcore', 'quad core')  # Official name
        return s

    @staticmethod
    def storage_str(storage: float) -> str:
        if storage >= 1000:
            return str(int(round(storage / 1000.0, 2)))
        else:
            return str(int(storage))
