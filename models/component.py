from __future__ import annotations

import pickle
import sys
from typing import Optional, Union, Type, List
from peewee import FloatField, CharField, IntegerField, ForeignKeyField

from factors.age_factor import AgeFactor
from models.model import BaseModel
from global_vars.model import Category, ReferenceValue, DdrType
from factors.perf_factor import PerfFactor
from utils.paths import models_path
# from scrapers.component import BenchmarkSpider, UserBenchmarkSpider

with open(models_path, 'rb') as file:
    models = pickle.load(file)


class Component(BaseModel):

    name = CharField()
    category = IntegerField()  # Category

    def __str__(self):
        return self.name + ' | ' + Category.labels[self.category]

    def get_child(self) -> Optional[Union[ComponentCpu, ComponentGpu]]:
        component_subtype_list = [None, ComponentCpu, ComponentGpu, ComponentRam, ComponentMotherboard, ComponentHdd,
                              ComponentSsd, ComponentCase, ComponentPsu, ComponentOs, ComponentPlayer]  # Based on model category label
        if self.category != Category.OTHER:
            return component_subtype_list[int(str(self.category))].get(component_subtype_list[int(str(self.category))].parent == self.id)
        else:
            return None

    def get_child_type(self) -> Optional[Union[Type[ComponentCpu], Type[ComponentGpu]]]:
        return type(self.get_child())

    def benchmark_net_value(self) -> FloatField:
        try:
            return self.get_child().benchmark_net_value()
        except Exception as e:
            return self.get_child().get_performance()

    def userbenchmark_value(self) -> FloatField:
        try:
            return self.get_child().userbenchmark_value()
        except Exception as e:
            return self.get_child().get_performance()

    def print(self):
        print("name: {} | category: {} | performance: {} "
              .format(self.name, Category.labels[self.category], str(self.benchmark_net_value())))

    @classmethod
    def create(cls, category: int, *args, **kwargs) -> Component:
        component = super().create(category=category, **kwargs)
        component_subtype_list = [None, ComponentCpu, ComponentGpu, ComponentRam, ComponentMotherboard, ComponentHdd,
                              ComponentSsd, ComponentCase, ComponentPsu, ComponentOs, ComponentPlayer]  # Based on model category label
        component_subtype = component_subtype_list[category]

        if component_subtype is not None:
            component_subtype.create(parent=component.id, **kwargs)

        return component

    @classmethod
    def exists(cls, name: str) -> int:
        query = cls.select().where((cls.name == name))
        if len(list(query)) > 0:
            return list(query)[0].id
        return -1

    @classmethod
    def get_pairs(cls, ref_perf: float, pairs_type: Union[Type[ComponentCpu], Type[ComponentGpu]],
                  algo: str = 'threshold', threshold: float = 0.3, n_best: int = 10) -> List[Component]:
        """ Get the list of best fitted components

        :param ref_perf: avg_score of the component
        :param pairs_type: ComponentCpu if ref_perf is gpu, ComponentGpu otherwise
        :param algo: algorithm {'threshold', 'n_best'}
        :param threshold: threshold to apply for 'threshold' algorithm
        :param n_best: n_best to apply for 'n_best' algorithm
        :return: list of best fitted components
        """
        if pairs_type == ComponentGpu:
            perf = 0.000003079964*ref_perf**3.753164
        else:
            perf = 27.85681*ref_perf**0.2794096

        if algo == 'threshold':
            perf_min = perf - (perf*threshold)
            perf_max = perf + (perf*threshold)
            return list(Component.select().join(pairs_type).where((pairs_type.userbenchmark_score > perf_min) & (pairs_type.userbenchmark_score < perf_max)))
        elif algo == 'n_best':
            n_best_list = [(abs(x.componentgpu.userbenchmark_score - perf), x) for x in Component.select(Component, pairs_type).join(pairs_type)]
            n_best_list = sorted(n_best_list, key=lambda x: x[0])
            return [x[1] for x in n_best_list][:n_best]
        else:
            return []

    @classmethod
    def get_component_pairs(cls, ref_comp: Component, algo: str = 'threshold', threshold: float = 0.3,
                            n_best: int = 10) -> List[Component]:
        if type(ref_comp.get_child()) is ComponentGpu:
            pairs_type = ComponentCpu
        elif type(ref_comp.get_child()) is ComponentCpu:
            pairs_type = ComponentGpu
        else:
            return []
        return cls.get_pairs(float(str(ref_comp.get_child().userbenchmark_score)), pairs_type, algo, threshold, n_best)


class ComponentGpu(BaseModel):
    value_model = 'perf_age_model'  # Possible values : 'linear_perf', 'best_value', 'perf_age_model'

    parent = ForeignKeyField(Component, primary_key=True)
    # benchmark.net
    benchmark_net_score = FloatField(default=0.0)
    # userbenchmark
    userbenchmark_score = FloatField(default=0.0)

    age = FloatField(default=0.0)  # In months

    # dx9 = FloatField(default=0.0)
    # dx10 = FloatField(default=0.0)
    # lighting = FloatField(default=0.0)
    # reflection = FloatField(default=0.0)
    # parallax = FloatField(default=0.0)

    def print(self):
        self.parent.print()

    def benchmark_net_value(self):
        if self.value_model == 'perf_model':
            from scrapers.component import BenchmarkSpider
            return self.benchmark_net_score * PerfFactor.get_prediction(models, BenchmarkSpider.name, Category.GPU, float(self.benchmark_net_score)) * ReferenceValue.GPU_FACTOR
        elif self.value_model == 'perf_age_model':
            from scrapers.component import BenchmarkSpider
            return self.benchmark_net_score *\
                   PerfFactor.get_prediction(models, BenchmarkSpider.name, Category.GPU, float(self.benchmark_net_score)) *\
                   AgeFactor.get_prediction(models, BenchmarkSpider.name, Category.GPU, float(self.age))
        elif self.value_model == 'best_value':
            return self.benchmark_net_score * ReferenceValue.GPU_BENCHMARK_NET * ReferenceValue.GPU_FACTOR
        else:
            return None

    def userbenchmark_value(self):
        if self.value_model == 'perf_model':
            from scrapers.component import UserBenchmarkSpider
            return self.userbenchmark_score * PerfFactor.get_prediction(models, UserBenchmarkSpider.name, Category.GPU, float(self.userbenchmark_score)) * ReferenceValue.GPU_FACTOR
        elif self.value_model == 'perf_age_model':
            from scrapers.component import UserBenchmarkSpider
            return self.userbenchmark_score *\
                   PerfFactor.get_prediction(models, UserBenchmarkSpider.name, Category.GPU, float(self.userbenchmark_score)) *\
                   AgeFactor.get_prediction(models, UserBenchmarkSpider.name, Category.GPU, float(self.age))
        elif self.value_model == 'best_value':
            return self.userbenchmark_score * ReferenceValue.GPU_USERBENCHMARK * ReferenceValue.GPU_FACTOR
        else:
            return None


class ComponentCpu(BaseModel):
    value_model = 'perf_model'  # Possible values : 'linear', 'best_value'

    parent = ForeignKeyField(Component, primary_key=True)
    # benchmark.net
    benchmark_net_score = FloatField(default=0.0)
    # userbenchmark
    userbenchmark_score = FloatField(default=0.0)

    age = FloatField(default=0.0)  # In months

    # normal = FloatField(default=0.0)
    # heavy = FloatField(default=0.0)
    # server = FloatField(default=0.0)
    # core_1 = FloatField(default=0.0)
    # core_2 = FloatField(default=0.0)
    # core_4 = FloatField(default=0.0)
    core_8 = FloatField(default=0.0)
    # core_64 = FloatField(default=0.0)

    def print(self):
        self.parent.print()

    def benchmark_net_value(self):
        if self.value_model == 'perf_model':
            from scrapers.component import BenchmarkSpider
            return self.benchmark_net_score * PerfFactor.get_prediction(models, BenchmarkSpider.name, Category.CPU, float(self.benchmark_net_score)) * ReferenceValue.CPU_FACTOR
        elif self.value_model == 'perf_age_model':
            from scrapers.component import BenchmarkSpider
            return self.benchmark_net_score *\
                   PerfFactor.get_prediction(models, BenchmarkSpider.name, Category.CPU, float(self.benchmark_net_score)) *\
                   AgeFactor.get_prediction(models, BenchmarkSpider.name, Category.CPU, float(self.age))
        elif self.value_model == 'best_value':
            return self.benchmark_net_score * ReferenceValue.CPU_BENCHMARK_NET * ReferenceValue.CPU_FACTOR
        else:
            return None

    def userbenchmark_value(self):
        if self.value_model == 'perf_model':
            from scrapers.component import UserBenchmarkSpider
            return self.userbenchmark_score * PerfFactor.get_prediction(models, UserBenchmarkSpider.name, Category.CPU, float(self.userbenchmark_score)) * ReferenceValue.CPU_FACTOR
        elif self.value_model == 'perf_age_model':
            from scrapers.component import UserBenchmarkSpider
            return self.userbenchmark_score *\
                   PerfFactor.get_prediction(models, UserBenchmarkSpider.name, Category.CPU, float(self.userbenchmark_score)) *\
                   AgeFactor.get_prediction(models, UserBenchmarkSpider.name, Category.CPU, float(self.age))
        elif self.value_model == 'best_value':
            return self.userbenchmark_score * ReferenceValue.CPU_USERBENCHMARK * ReferenceValue.CPU_FACTOR
        else:
            return None


class ComponentRam(BaseModel):
    parent = ForeignKeyField(Component, primary_key=True)
    amount = FloatField()  # In Go
    ddr = IntegerField()  # DdrType
    speed = FloatField()  # In Mhz

    def print(self):
        self.parent.print()

    def get_performance(self):
        return self.amount * ReferenceValue.RAM[self.ddr]


class ComponentMotherboard(BaseModel):
    parent = ForeignKeyField(Component, primary_key=True)
    mb_type = IntegerField()  # MotherboardType

    def print(self):
        self.parent.print()

    def get_performance(self):
        return ReferenceValue.MB * ReferenceValue.MB_FACTOR[self.mb_type]


class ComponentHdd(BaseModel):
    parent = ForeignKeyField(Component, primary_key=True)
    amount = FloatField()

    def print(self):
        self.parent.print()

    def get_performance(self):
        return self.amount * ReferenceValue.HDD


class ComponentSsd(BaseModel):
    parent = ForeignKeyField(Component, primary_key=True)
    amount = FloatField()

    def print(self):
        self.parent.print()

    def get_performance(self):
        return self.amount * ReferenceValue.SSD


class ComponentCase(BaseModel):
    parent = ForeignKeyField(Component, primary_key=True)
    case_type = IntegerField()  # CaseType

    def print(self):
        self.parent.print()

    def get_performance(self):
        return ReferenceValue.CASE * ReferenceValue.CASE_FACTOR[self.case_type]


class ComponentPsu(BaseModel):
    parent = ForeignKeyField(Component, primary_key=True)
    amount = FloatField()  # Watt

    def print(self):
        self.parent.print()

    def get_performance(self):
        return self.amount * ReferenceValue.PSU


class ComponentOs(BaseModel):
    parent = ForeignKeyField(Component, primary_key=True)
    os = IntegerField()  # OsType

    def print(self):
        self.parent.print()

    def get_performance(self):
        return ReferenceValue.OS * ReferenceValue.OS_FACTOR[self.os]


class ComponentPlayer(BaseModel):
    parent = ForeignKeyField(Component, primary_key=True)
    player_type = IntegerField()  # PlayerType

    def print(self):
        self.parent.print()

    def get_performance(self):
        return ReferenceValue.PLAYER * ReferenceValue.PLAYER_FACTOR[self.player_type]
