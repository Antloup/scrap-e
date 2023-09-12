import re
from typing import List, Union

from global_vars import Category
from guesser.guesser import Guesser
from models import Component, ComponentCpu, ComponentGpu
from scrapers import BasicSpider, scrapy


class UserBenchmarkSpider(BasicSpider):
    name = 'user_benchmark'
    form_data = {'tableDataForm': "tableDataForm",
                 'tableDataForm:tdahinid': "",
                 # 'javax.faces.ViewState':"-834908156689577985:-563619457431236688",
                 'javax.faces.source': "tableDataForm:j_idt218",
                 'javax.faces.partial.event': "click",
                 'javax.faces.partial.execute': "tableDataForm:j_idt218 tableDataForm",
                 'javax.faces.partial.render': "tableDataForm:mhtddynsbc tableDataForm:mhtddyntac mhtdsbjsform mhtdcompform",
                 'PGMP': "1",
                 'NIMP': "50",
                 'javax.faces.behavior.event': "action",
                 'javax.faces.partial.ajax': "true"
                 }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_delay = 24.42

    def start_requests(self):
        urls = [
            'https://gpu.userbenchmark.com/',
            'https://cpu.userbenchmark.com/'
        ]

        for i, url in enumerate(urls):
            yield scrapy.Request(url, meta={'cookiejar': (i+1)}, callback=self.parse)

    def parse(self, response):
        # # number_component = response.xpath("(//span[@id='tableDataForm:mhtddynsbc']/div/text())[1]").get()\
        # #     .replace(' ','').replace(',','')
        number_pages = re.search(r'\s([0-9]+)$',response.xpath('//nav/ul/li/a/text()').get()).group(1)

        for i in range(int(number_pages)):
            data = dict(self.form_data)
            data['PGMP'] = str(i+1)
            yield scrapy.http.FormRequest.from_response(response=response, formdata=data, dont_click=True,
                                                  callback=self.parse_list, meta={'cookiejar': response.meta['cookiejar']})

    def parse_list(self, response):
        content = response.xpath("//update[@id='tableDataForm:mhtddyntac']/text()").get()

        if 'gpu.' in response.url:
            comp_category = Category.GPU
        else:
            comp_category = Category.CPU

        len_component = len(scrapy.Selector(text=content).xpath("//table/tbody/tr[@data-id]"))

        print('Number of components:{}'.format(len_component))
        component_processed = 0
        for component in scrapy.Selector(text=content).xpath("//table/tbody/tr[@data-id]"):
            avg_score = float(component.xpath("td[5]/div/div/text()").get())
            if (comp_category == Category.GPU and avg_score < 5.47) or \
                    (comp_category == Category.CPU and avg_score < 35.5):  # Threshold is 8800 GT / Intel Core2 Duo E6300
                continue
            name = component.xpath("td[2]//a[@class='nodec']/text()").get()
            comps, _, _ = Guesser.guess_single_components(comp_category, Guesser.trim(name), skip_nogo=True)
            if len(comps) == 0:
                print('unk name {}'.format(name))
                continue
            if len(comps) > 1:
                print('Multiples name for {}'.format(name))
                continue

            if comp_category == Category.GPU:
                age = component.xpath("td[7]//div[1]/text()").get()
            else:
                age = component.xpath("td[9]//div[1]/text()").get()
            try:
                age = float(age.replace('+',''))
            except:
                age = -1.0  # TODO : deal with it

            comp: Union[ComponentCpu, ComponentGpu] = comps[0].get_child()
            comp.userbenchmark_score = avg_score
            comp.age = age
            comp.save()
            component_processed += 1

        print('Components processed:{}/{}'.format(component_processed,len_component))

        # for comp in scrapy.Selector(text=content).xpath("//a[@class='nodec' and not(@style)]"):
        #     # print(comp.xpath('@href').get())
        #     Component.select().where(Component.name)
        #     # yield scrapy.Request(comp.xpath('@href').get(), callback=self.parse_component)

    # def parse_component(self, response):
    #     name = response.xpath("//h1[@class='pg-head-title']/a/text()").get().replace('-', ' ')
    #     scores: dict = {}
    #     avg_cat_score = []
    #     avg_score = float(response.xpath("//div[@class='uc-score uc-score-large']/a/text()").get())
    #     for table in response.xpath("//table[@class='mcs-table']"):
    #         for tr in table.xpath("tbody/tr"):
    #             if len(tr.xpath("td/span[@class='graytext']")) != 0:
    #                 avg_cat_score.append(float(tr.xpath("td/span[@class='graytext']/text()").get()))
    #             else:
    #                 key = tr.xpath('td[2]/text()').get().lower().replace(' ', '')
    #                 s = re.search(r'(([0-9]+)-)?(.*?)$',key)
    #                 key = s.group(3) if s.group(1) is None else s.group(3) + '_' + s.group(2)
    #                 scores[key] = float(tr.xpath('td[2]/span/text()').get())
    #
    #     kwargs = dict(scores)
    #     kwargs['avg_score'] = avg_score
    #
    #     if 'gpu.' in response.url:
    #         comp_category = Category.GPU
    #         if len(avg_cat_score) != 2:
    #             print('Wrong number of categories for name {}'.format(name))
    #             return 0
    #         kwargs['dx9'] = avg_cat_score[0]
    #         kwargs['dx10'] = avg_cat_score[1]
    #     else:
    #         comp_category = Category.CPU
    #         if len(avg_cat_score) != 3:
    #             print('Wrong number of categories for name {}'.format(name))
    #             return 0
    #         kwargs['normal'] = avg_cat_score[0]
    #         kwargs['heavy'] = avg_cat_score[1]
    #         kwargs['server'] = avg_cat_score[2]
    #
    #     comps, _, _ = Guesser.guess_single_components(comp_category, Guesser.trim(name), skip_nogo=True)
    #     if len(comps) == 0:
    #         print('unk name {}'.format(name))
    #         return 0
    #     comp: Component = comps[0].get_child()
    #     for key, value in kwargs.items():
    #         setattr(comp, key, value)
    #     comp.update()
