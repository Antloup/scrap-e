from typing import Optional

import yaml
import sys
from PyQt5.QtWidgets import QWidget, QGroupBox, QTableWidget, QComboBox, QVBoxLayout, QHBoxLayout, QLabel, \
    QAbstractItemView, QHeaderView, QPushButton, QListWidgetItem
from peewee import fn

from global_vars import Category, Condition, Website
from PyQt5.QtCore import Qt, QUrl
from PyQt5 import QtCore

from models import Component, DealComponent, Deal, ComponentCpu, ComponentGpu, db
from qt_ext.deal_qtable_widget_item import DealQTableWidgetItem
from PyQt5.QtGui import QDesktopServices
from utils.paths import db_config_path


class DbWidget(QWidget):

    update = QtCore.pyqtSignal(Deal)

    def __init__(self, group_box=False):

        super().__init__()

        # Properties
        self.db_config: dict = yaml.load(open(db_config_path), Loader=yaml.FullLoader)

        if group_box:
            self.db_group_box = QGroupBox('Database')
        else:
            self.db_group_box = QGroupBox('')
            self.db_group_box.setStyleSheet("QGroupBox{border:0;}")
        self.db_table = QTableWidget()
        self.db_filter_combo_box = QComboBox()

        # Init

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        group_box_layout = QVBoxLayout()
        self.db_group_box.setLayout(group_box_layout)
        main_layout.addWidget(self.db_group_box)

        line_layout = QHBoxLayout()
        group_box_layout.addLayout(line_layout)

        line_layout.addWidget(QLabel('Filter:'))

        # self.db_filter_combo_box.setStyleSheet("")
        self.db_filter_combo_box.addItems(['ALL'] + Category.labels)
        self.db_filter_combo_box.setEnabled(False)  # TODO
        self.db_filter_combo_box.currentIndexChanged.connect(self.db_filter_combo_box_changed)
        line_layout.addWidget(self.db_filter_combo_box)

        self.db_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.db_table.setSortingEnabled(True)
        self.db_table.setRowCount(0)
        table_header = ['Id', 'Type', 'Title', 'Value N', 'Benef N', 'Value U', 'Benef U', 'Price', 'Date', 'Website']
        self.db_table.setColumnCount(len(table_header))
        self.db_table.setHorizontalHeaderLabels(table_header)
        self.db_table.itemDoubleClicked.connect(self.table_item_clicked)
        self.db_table.currentItemChanged.connect(self.table_item_selected)
        self.db_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.db_table.setColumnHidden(0, True)
        for i, item in enumerate([(QHeaderView.Fixed, 80), (QHeaderView.Stretch, 100), (QHeaderView.Fixed, 50),
                                  (QHeaderView.Fixed, 50), (QHeaderView.Fixed, 50), (QHeaderView.Fixed, 50),
                                  (QHeaderView.Fixed, 50), (QHeaderView.Fixed, 100), (QHeaderView.Fixed, 50)]):
            self.db_table.horizontalHeader().setSectionResizeMode(i + 1, item[0])
            self.db_table.setColumnWidth(i + 1, item[1])
        self.db_table.setMinimumWidth(self.db_table.horizontalHeader().length() + 20)
        group_box_layout.addWidget(self.db_table)

        line_layout = QHBoxLayout()
        group_box_layout.addLayout(line_layout)

        button = QPushButton('Clear Deal DB')
        button.clicked.connect(self.db_clear_button_clicked)
        line_layout.addWidget(button)

        button = QPushButton('Refresh DB')
        button.clicked.connect(self.db_refresh_button_clicked)
        line_layout.addWidget(button)

        self.db_refresh_button_clicked()

    def db_refresh_button_clicked(self):
        self.update_config()
        min_cpu_perf, min_gpu_perf = 0, 0
        cpu_label = Category.labels[Category.CPU]
        gpu_label = Category.labels[Category.GPU]
        other_label = Category.labels[Category.OTHER]
        cpu_ref = self.db_config[cpu_label]['ref']
        gpu_ref = self.db_config[gpu_label]['ref']
        if cpu_ref != '':
            try:
                min_cpu_perf = Component.get(Component.name == cpu_ref).get_child().benchmark_net_score
            except:
                pass
        if gpu_ref != '':
            try:
                min_gpu_perf = Component.get(Component.name == gpu_ref).get_child().benchmark_net_score
            except:
                pass

        query_list = []

        single_component_deal = DealComponent.select() \
            .group_by(DealComponent.deal) \
            .having(fn.COUNT(DealComponent.component_base) == 1)

        # CPU query
        if self.db_config[cpu_label]['active']:
            query = Deal.select().join(DealComponent).join(Component).join(ComponentCpu) \
                .where((DealComponent.id.in_(single_component_deal)) &
                       (Component.category == Category.CPU) &
                       (ComponentCpu.benchmark_net_score >= min_cpu_perf) &
                       (~Component.name.contains('xeon') &
                        (Deal.benchmark_net_value >= self.db_config[cpu_label]['min_value_n']) &
                        (Deal.userbenchmark_value >= self.db_config[cpu_label]['min_value_u']) &
                        (Deal.benchmark_net_benefit_value >= self.db_config[cpu_label]['min_benef_n']) &
                        (Deal.userbenchmark_benefit_value >= self.db_config[cpu_label]['min_benef_u']) &
                        (Deal.condition != Condition.NOT_WORKING))) \
                .group_by(Deal) \
                .order_by(Deal.benchmark_net_value.desc())

            query_list += list(query)

        # GPU query
        if self.db_config[gpu_label]['active']:
            query = Deal.select().join(DealComponent).join(Component).join(ComponentGpu) \
                .where((DealComponent.id.in_(single_component_deal)) &
                       (Component.category == Category.GPU) &
                       (ComponentGpu.benchmark_net_score >= min_gpu_perf) &
                       (Deal.benchmark_net_value >= self.db_config[gpu_label]['min_value_n']) &
                       (Deal.userbenchmark_value >= self.db_config[gpu_label]['min_value_u']) &
                       (Deal.benchmark_net_benefit_value >= self.db_config[gpu_label]['min_benef_n']) &
                       (Deal.userbenchmark_benefit_value >= self.db_config[gpu_label]['min_benef_u']) &
                       (Deal.condition != Condition.NOT_WORKING)) \
                .group_by(Deal) \
                .order_by(Deal.benchmark_net_value.desc())

            query_list += list(query)

        # Other query
        if self.db_config[other_label]['active']:
            query = Deal.select().distinct().join(DealComponent).join(Component) \
                .where((DealComponent.id.not_in(single_component_deal)) &
                       (Deal.benchmark_net_value >= self.db_config[other_label]['min_value']) &
                       (Deal.benchmark_net_benefit_value >= self.db_config[other_label]['min_benef'])) \
                .group_by(Deal) \
                .order_by(Deal.benchmark_net_value.desc())

            query_list += list(query)

        query_list = set(query_list)  # Remove potential duplicates

        self.db_table.setRowCount(len(query_list))
        self.db_table.setSortingEnabled(False)
        for i, deal in enumerate(query_list):
            for j, item in enumerate([str(deal.id), Category.labels[deal.category], deal.title,
                                      str(round(deal.benchmark_net_value, 3)), str(round(deal.benchmark_net_benefit_value, 2)),
                                      str(round(deal.userbenchmark_value, 3)), str(round(deal.userbenchmark_benefit_value, 2)),
                                      str(round(deal.full_price, 3)), deal.upload_date.strftime("%d-%m-%y %H:%M"),
                                      Website.labels[deal.website]]):
                self.db_table.setItem(i, j, DealQTableWidgetItem(item))
        self.db_table.setSortingEnabled(True)

    def db_clear_button_clicked(self):
        db.drop_tables([DealComponent, Deal])
        db.create_tables([DealComponent, Deal])
        self.db_refresh_button_clicked()

    def db_filter_combo_box_changed(self):
        print('todo')

    def table_item_clicked(self, item: DealQTableWidgetItem):
        deal_id = int(self.db_table.item(item.row(), 0).text())
        deal = Deal.get_by_id(deal_id)
        QDesktopServices.openUrl(QUrl(deal.url))

    def table_item_selected(self, current: Optional[QListWidgetItem], previous: Optional[QListWidgetItem]):
        if current is None:
            return
        deal_id = int(self.db_table.item(current.row(), 0).text())
        self.update.emit(Deal.get_by_id(deal_id))

    def update_config(self):
        self.db_config: dict = yaml.load(open(db_config_path), Loader=yaml.FullLoader)
