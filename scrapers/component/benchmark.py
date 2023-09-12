import re

from models.component import Component, ComponentGpu, ComponentCpu
from global_vars.model import Category
from scrapers import BasicSpider
from global_vars import ScraperStatus


class BenchmarkSpider(BasicSpider):
    name = 'benchmark_net'
    start_urls = [
        'https://www.videocardbenchmark.net/gpu_list.php',
        'https://www.cpubenchmark.net/cpu_list.php'
    ]

    def parse(self, response):
        comp_category: int = Category.GPU
        if 'www.cpubenchmark.net' in str(response):
            comp_category = Category.CPU

        for component in response.xpath("//table[@id='cputable']/tbody/tr[@id]"):
            component_name: str = component.xpath("td[1]/a/text()").get()
            component_name = component_name.replace('-', ' ')
            component_name = re.sub(r' @ .*$', '', component_name)
            if ' + ' in component_name:
                # Do not handle multiple GPUs
                continue
            component_perf: float = float(component.xpath("td[2]/text()").get().replace(',', ''))

            if (comp_category == Category.GPU and component_perf < 541) or\
                    (comp_category == Category.CPU and component_perf < 526):  # Threshold is 8800 GT / Intel Core2 Duo E6300
                continue

            if ' / ' in component_name:
                component_names = component_name.split(' / ')
                first_word = component_names[0].split(' ')[0]
                for i in range(1, len(component_names)):
                    if component_names[i] == 'M370X':  # Small special case
                        component_names[i] = 'R9 ' + component_names[i]
                    component_names[i] = first_word + ' ' + component_names[i]
            else:
                component_names = [component_name]

            for name in component_names:
                yield {
                    'OBJ_TYPE': Component,
                    'EXIST': Component.exists(name),
                    'UPDATE': True,
                    'ARGS': {
                        'category': comp_category,
                        'benchmark_net_score': component_perf,
                        'name': name
                    }
                }

        self.send_status(ScraperStatus.PAGE_DONE, [str(response)])
