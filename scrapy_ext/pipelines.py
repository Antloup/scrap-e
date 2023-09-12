import random
import string

import scrapy
from scrapy.exceptions import DropItem
from utils.paths import img_data_path
from urllib.request import urlretrieve
import re


class MyImagesPipeline:

    def process_item(self, item, spider):
        item['ARGS']['thumb_path'] = ''
        if 'thumb_url' in item['ARGS'] and item['ARGS']['thumb_url'] != '' and item['ARGS']['thumb_url'] is not None\
                and item['EXIST'] == -1:
            img_ext = re.search("(.*)(\..*?$)", item['ARGS']['thumb_url']).group(2)
            img_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20)) + img_ext
            urlretrieve(item['ARGS']['thumb_url'], img_data_path + '/' + img_name)
            item['ARGS']['thumb_path'] = img_name
        return item


class PeeweePipeline:

    def process_item(self, item, spider):
        if item['EXIST'] == -1:
            item['OBJ_TYPE'].create(**item['ARGS'])
        elif item['UPDATE']:
            item['OBJ_TYPE'].update(**item['ARGS']).where(item['OBJ_TYPE'].id == item['EXIST'])
        return item
