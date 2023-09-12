import re
from datetime import datetime
from typing import List, Set, Optional

from peewee import ForeignKeyField, DeferredForeignKey, TextField, FloatField, IntegerField, fn, DateTimeField, \
    BigIntegerField, CharField

from models.component import Component
from models.model import BaseModel
from global_vars.model import Category, DealType, DealStatus, Website, Condition, ReferenceValue, DealClass


class DealComponent(BaseModel):
    component_base = ForeignKeyField(Component, backref=None)
    deal = DeferredForeignKey('Deal', backref=None)


class DealComponentPartial(BaseModel):
    # TODO: use at some point
    deal = DeferredForeignKey('Deal', backref=None)
    component_category = IntegerField()  # Category
    partial_name = CharField()


class Deal(BaseModel):
    title = TextField()
    price = FloatField(default=-1.0)
    full_price = FloatField(default=-1.0)  # Include shipping price
    url = TextField(default='')
    thumb_url = TextField(default='')
    thumb_path = TextField(default='')
    benchmark_net_value = FloatField(default=0.0)
    benchmark_net_benefit_value = FloatField(default=0.0)
    userbenchmark_value = FloatField(default=0.0)
    userbenchmark_benefit_value = FloatField(default=0.0)
    main_item_type = IntegerField(default=Category.OTHER)  # Category  # TODO: put deprecated
    type = IntegerField(default=DealType.UNK)  # DealType
    status = IntegerField(default=DealStatus.UNK)  # DealStatus
    listing_type = IntegerField(null=True)   # Listing
    website = IntegerField(default=Website.OTHER)  # Website
    item_id = BigIntegerField(default=0)  # Item id on the website
    condition = IntegerField(default=Condition.OTHER)
    category = IntegerField(default=Category.OTHER)  # ModelCategory
    upload_date = DateTimeField(default=datetime.now)
    label = IntegerField(default=DealClass.UNDEF)

    def get_components(self) -> List[DealComponent]:
        return list(DealComponent.select().where(DealComponent.deal == self.id))

    def delete_components(self):
        q = DealComponent.delete().where(DealComponent.deal == self)
        q.execute()

    def add_components(self, components: List[Component]):
        for comp in components:
            DealComponent.create(deal=self, component_base=comp)

    def get_main_item_type(self) -> int:
        cpu: int = 0
        gpu: int = 0
        for component in self.get_components():
            if component.component_base.category == Category.CPU:
                cpu += 1
            elif component.component_base.category == Category.GPU:
                gpu += 1
        if cpu > 0 and gpu == 0:
            return Category.CPU
        elif gpu > 0 and cpu == 0:
            return Category.GPU
        else:
            return Category.OTHER

    def print(self):
        component_name = 'UNK' if len(self.get_components()) == 0 else self.get_components()[0].component_base.name
        print("category: {} | type: {} | value: {} \t| guessed_model: {} \t| {}"
              .format(Category.labels[self.get_main_item_type()], DealType.labels[self.type],
                      str(self.benchmark_net_value), component_name, self.url))

    @classmethod
    def exists(cls, item_id: int, website: int, url: str, category: int, last_update=None) -> int:
        query = Deal.select()
        if last_update is not None:
            query = query.where(Deal.upload_date > last_update)
        query = query.where((Deal.item_id == item_id) & (Deal.website == website) & (Deal.url == url) & (Deal.category == category))
        if len(list(query)) > 0:
            return list(query)[0].id
        return -1

    @classmethod
    def create(cls, components: List[Component], *args, **kwargs) -> bool:
        """
        :param components: base component list (can be obtained with guess_components)
        :param args:
        :param kwargs: Deal kwargs
        :return: True if deal already existed, false otherwise
        """
        deal = super().create(**kwargs, value=0.0, main_item_type=0)
        for component in components:
            DealComponent.create(component_base=component, deal=deal.id)
        deal.main_item_type = deal.get_main_item_type()
        deal.refresh_value(save=True)
        return deal

    def refresh_value(self, save: bool = True) -> float:
        self.benchmark_net_value: float = 0.0
        self.userbenchmark_value: float = 0.0
        components = Component.select().join(DealComponent).where(DealComponent.deal == self.id)
        for component in components:
            self.benchmark_net_value += component.benchmark_net_value()
            self.userbenchmark_value += component.userbenchmark_value()
        self.benchmark_net_benefit_value = self.benchmark_net_value / ReferenceValue.BENEFIT_VALUE - self.full_price
        self.benchmark_net_value /= self.full_price
        self.userbenchmark_benefit_value = self.userbenchmark_value / ReferenceValue.BENEFIT_VALUE - self.full_price
        self.userbenchmark_value /= self.full_price
        if save:
            self.save()
        return self.benchmark_net_value

    @classmethod
    def print_report(cls):
        print('--- STATUS ---')
        total = 0
        for status in [DealStatus.UNK, DealStatus.SURE, DealStatus.MIXED]:
            count = Deal.select().where(Deal.status == status).count()
            total += count
            print(DealStatus.labels[status] + ': ' + str(count), end='\t')
        print('Total: {}'.format(total))

        print('--- TYPES ---')
        total = 0
        for deal_type in [DealType.UNK, DealType.SINGLE_ITEM, DealType.USELESS, DealType.LOT, DealType.MULTIPLE_ITEM]:
            count = Deal.select().where(Deal.type == deal_type).count()
            total += count
            print(DealType.labels[deal_type] + ': ' + str(count), end='\t')
        print('Total: {}'.format(total))

