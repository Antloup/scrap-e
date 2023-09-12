from typing import List, Optional

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGridLayout
from peewee import fn

from global_vars import DealClass
from models import Deal
from utils.paths import img_data_path
from PyQt5.QtCore import Qt
from PyQt5 import QtCore

price_format = '{} + {} = {}'
link_format = "<a href=\"{}\">{}</a>"


class LabelerWidget(QWidget):

    update = QtCore.pyqtSignal(Deal)

    def __init__(self, group_box=False):
        super().__init__()

        if group_box:
            self.labeler_group_box = QGroupBox('Labeler')
        else:
            self.labeler_group_box = QGroupBox('')
            self.labeler_group_box.setStyleSheet("QGroupBox{border:0;}")
        self.focus_button = QPushButton('Focus me')
        self.progression_label = QLabel('0/0')
        self.thumb_img = QLabel('IMG')
        self.title = QLabel('UNK')
        self.price_label = QLabel('Price:')
        self.price = QLabel(price_format.format(0.0, 0.0, 0.0))
        self.main_component_label = QLabel('Main component:')
        self.main_component = QLabel('Model')
        self.unk_button = QPushButton('UNK')
        self.fake_button = QPushButton('Fake')
        self.real_button = QPushButton('Real')
        self.skip_button = QPushButton('Skip')
        self.deals: List[Deal] = list(Deal.select().where(Deal.label == DealClass.UNDEF))
        self.current_deal: Optional[Deal] = None

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.labeler_group_box)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        group_box_layout = QVBoxLayout()
        group_box_layout.setAlignment(Qt.AlignCenter)
        self.labeler_group_box.setLayout(group_box_layout)

        group_box_layout.addWidget(self.focus_button)
        self.focus_button.clicked.connect(self.set_focus)

        group_box_layout.addWidget(self.progression_label)
        self.progression_label.setAlignment(Qt.AlignCenter)
        self.prog_tot = list(Deal.select(fn.COUNT(Deal.id).alias('tot')).dicts())[0]['tot']
        self.prog_remain = list(Deal.select(fn.COUNT(Deal.id).alias('tot')).where(Deal.label == DealClass.UNDEF).dicts())[0]['tot'] + 1

        self.thumb_img.setAlignment(Qt.AlignCenter)
        group_box_layout.addWidget(self.thumb_img)

        self.title.setAlignment(Qt.AlignCenter)
        self.title.setText(link_format.format('www.google.com', 'Title'))
        self.title.setTextFormat(Qt.RichText)
        self.title.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.title.setOpenExternalLinks(True)
        group_box_layout.addWidget(self.title)

        line_layout = QHBoxLayout()
        line_layout.setAlignment(Qt.AlignCenter)
        self.price_label.setAlignment(Qt.AlignRight)
        self.price.setAlignment(Qt.AlignLeft)
        line_layout.addWidget(self.price_label)
        line_layout.addWidget(self.price)
        group_box_layout.addLayout(line_layout)

        line_layout = QHBoxLayout()
        line_layout.setAlignment(Qt.AlignCenter)
        self.main_component_label.setAlignment(Qt.AlignRight)
        self.main_component.setAlignment(Qt.AlignLeft)
        line_layout.addWidget(self.main_component_label)
        line_layout.addWidget(self.main_component)
        group_box_layout.addLayout(line_layout)

        grid_layout = QGridLayout()
        group_box_layout.addLayout(grid_layout)

        grid_layout.addWidget(self.real_button, 0, 1)
        grid_layout.addWidget(self.unk_button, 1, 0)
        grid_layout.addWidget(self.fake_button, 1, 1)
        grid_layout.addWidget(self.skip_button, 1, 2)
        self.unk_button.clicked.connect(self.unk_button_clicked)
        self.fake_button.clicked.connect(self.fake_button_clicked)
        self.real_button.clicked.connect(self.real_button_clicked)
        self.skip_button.clicked.connect(self.skip_button_clicked)

        self.skip_button_clicked()

    def set_focus(self):
        self.setFocus()
        if self.current_deal is not None:
            self.update.emit(self.current_deal)

    def unk_button_clicked(self):
        self.current_deal.label = DealClass.UNK
        self.current_deal.save()
        self.skip_button_clicked()

    def fake_button_clicked(self):
        self.current_deal.label = DealClass.FAKE
        self.current_deal.save()
        self.skip_button_clicked()

    def real_button_clicked(self):
        self.current_deal.label = DealClass.REAL
        self.current_deal.save()
        self.skip_button_clicked()

    def skip_button_clicked(self):
        self.current_deal = self.deals.pop() if len(self.deals) > 0 else None
        if self.current_deal is not None:
            self.prog_remain -= 1
            self.progression_label.setText(str(self.prog_tot - self.prog_remain) + '/' + str(self.prog_tot))
            self.deal_refresh_data(self.current_deal)
            self.update.emit(self.current_deal)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.unk_button_clicked()
        if event.key() == Qt.Key_Right:
            self.skip_button_clicked()
        if event.key() == Qt.Key_Up:
            self.real_button_clicked()
        if event.key() == Qt.Key_Down:
            self.fake_button_clicked()
        event.accept()

    def deal_refresh_data(self, deal: Deal):
        try:
            self.title.setText(link_format.format(deal.url, deal.title))
            self.price.setText(price_format.format(round(deal.price, 2), round(deal.full_price - deal.price,2) ,round(deal.full_price,2)))
            self.thumb_img.setPixmap(QPixmap(img_data_path + '/' + deal.thumb_path))
            self.main_component.setText(deal.get_components()[0].component_base.name)
        except Exception as e:
            print(e)

