from typing import Optional, List, Tuple

from PyQt5.QtWidgets import QWidget, QGroupBox, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout, QCompleter, \
    QHBoxLayout

from global_vars import Category
from models import Deal, Component, ComponentCpu, ComponentGpu, ComponentRam, ComponentMotherboard, ComponentHdd,\
    ComponentSsd, ComponentCase, ComponentPsu, ComponentOs, ComponentPlayer
from PyQt5.QtCore import Qt


class DealWidget(QWidget):

    def __init__(self):
        super().__init__()

        # Properties
        self.deal_group_box = QGroupBox('Deal details')
        self.deal_name_label = QLabel('UNK')
        self.deal_current: Optional[Deal] = None
        self.deal_number_rows = len(Category.labels) - 1
        self.deal_price_edit = QLineEdit()
        self.deal_components: List[Tuple[QComboBox, QLineEdit, QLineEdit]] = []
        self.deal_overall_value = QLabel('0.0')
        self.deal_save_button = QPushButton('Save Deal')
        self.deal_clear_button = QPushButton('Clear')
        self.deal_completer_name = [['Other'],
                                    [x.parent.name for x in list(ComponentCpu.select().join(Component))],
                                    [x.parent.name for x in list(ComponentGpu.select().join(Component))],
                                    [x.parent.name for x in list(ComponentRam.select().join(Component))],
                                    [x.parent.name for x in list(ComponentMotherboard.select().join(Component))],
                                    [x.parent.name for x in list(ComponentHdd.select().join(Component))],
                                    [x.parent.name for x in list(ComponentSsd.select().join(Component))],
                                    [x.parent.name for x in list(ComponentCase.select().join(Component))],
                                    [x.parent.name for x in list(ComponentPsu.select().join(Component))],
                                    [x.parent.name for x in list(ComponentOs.select().join(Component))],
                                    [x.parent.name for x in list(ComponentPlayer.select().join(Component))]]

        # Init
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        self.deal_price_edit.textChanged.connect(lambda: self.refresh_value())
        group_box_layout = QVBoxLayout()
        self.deal_group_box.setLayout(group_box_layout)
        main_layout.addWidget(self.deal_group_box)

        line_layout = QHBoxLayout()
        group_box_layout.addLayout(line_layout)
        self.deal_name_label.setAlignment(Qt.AlignCenter)
        line_layout.addWidget(self.deal_name_label)

        for i in range(self.deal_number_rows):
            line_layout = QHBoxLayout()

            combo_box_type = QComboBox()
            combo_box_type.addItems(Category.labels)
            line_layout.addWidget(combo_box_type)

            completer = QCompleter([])
            combo_box_type.currentIndexChanged.connect(lambda val, c=completer: self.combo_box_changed(val, c))
            completer.setFilterMode(Qt.MatchContains)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            component_edit = QLineEdit()
            component_edit.textChanged.connect(lambda: self.refresh_value())
            component_edit.setCompleter(completer)
            line_layout.addWidget(component_edit)

            x_label = QLabel('x')
            line_layout.addWidget(x_label)

            num_component_edit = QLineEdit()
            num_component_edit.textChanged.connect(lambda: self.refresh_value())
            num_component_edit.setFixedWidth(30)
            line_layout.addWidget(num_component_edit)

            group_box_layout.addLayout(line_layout)

            self.deal_components.append((combo_box_type, component_edit, num_component_edit))

        line_layout = QHBoxLayout()
        price_label = QLabel('Price:')
        line_layout.addWidget(price_label)
        self.deal_price_edit.setFixedWidth(50)
        line_layout.addWidget(self.deal_price_edit)

        price_cur_label = QLabel('€')
        line_layout.addWidget(price_cur_label)

        value_label = QLabel('Overall value:')
        line_layout.addWidget(value_label)
        line_layout.addWidget(self.deal_overall_value)

        group_box_layout.addLayout(line_layout)

        line_layout = QHBoxLayout()

        self.deal_clear_button.clicked.connect(self.deal_clear_button_clicked)
        line_layout.addWidget(self.deal_clear_button)

        self.deal_save_button.clicked.connect(self.deal_save_button_clicked)
        line_layout.addWidget(self.deal_save_button)

        group_box_layout.addLayout(line_layout)
        self.deal_clear_button_clicked()

    def refresh_value(self) -> Tuple[float, float]:
        benchmark_net_value: float = 0.0
        userbenchmark_value: float = 0.0
        for component in self.deal_components:
            comp_cat, comp_name, comp_num = component
            comp = list(Component.select().where(
                (Component.category == int(comp_cat.currentIndex())) & (Component.name == comp_name.text())))
            if len(comp) == 0:
                continue
            comp = comp[0]
            try:
                multiply = int(comp_num.text())
            except:
                multiply = 1
            benchmark_net_value += multiply * comp.benchmark_net_value()
            userbenchmark_value += multiply * comp.userbenchmark_value()

        try:
            price = max(float(self.deal_price_edit.text()), 0.1)  # Avoid divide by 0
        except:
            price = 1.0
        benchmark_net_value = benchmark_net_value / price
        userbenchmark_value = userbenchmark_value / price
        overall_value = (benchmark_net_value + userbenchmark_value) / 2
        self.deal_overall_value.setText(str(round(benchmark_net_value, 3)) + '/' + str(round(userbenchmark_value, 3)))
        if overall_value < 1.0:
            self.deal_overall_value.setStyleSheet("font-weight: bold; color: red;")
        elif overall_value < 1.2:
            self.deal_overall_value.setStyleSheet("font-weight: bold; color: orange;")
        else:
            self.deal_overall_value.setStyleSheet("font-weight: bold; color: green;")
        return benchmark_net_value, userbenchmark_value

    def combo_box_changed(self, value: int, completer: QCompleter):
        model = completer.model()
        model.setStringList(self.deal_completer_name[value])

    def deal_clear_button_clicked(self, value=0):
        self.deal_current = None
        self.deal_price_edit.setText('1.0')
        self.deal_name_label.setText('UNK')
        for i, component in enumerate(self.deal_components):
            index = i % len(Category.labels) + 1
            comp_cat, comp_name, comp_num = component
            comp_cat.setCurrentIndex(index)
            comp_name.setText('')
            self.combo_box_changed(index, comp_name.completer())
            comp_num.setText('1')

    def deal_save_button_clicked(self):
        if self.deal_current is None:
            print('No deal to save')
            return
        is_valid: bool = True
        components: List[Component] = []
        for component in self.deal_components:
            if component[1].text() == '':
                continue
            comp = list(Component.select().where(Component.name == component[1].text()))
            comp = comp[0] if len(comp) > 0 else None
            if comp is not None:
                components.append(comp)
            else:
                is_valid = False
        if is_valid:
            self.deal_current.delete_components()
            self.deal_current.add_components(components)
            self.deal_current.full_price = float(self.deal_price_edit.text())
            self.deal_current.refresh_value()
            self.deal_current.save()
            print('Deal updated')
        else:
            print('Some names aren\'t valid')


    def deal_refresh_data(self, deal: Deal):
        self.deal_clear_button_clicked()
        self.deal_current = deal
        text = "<a href=\"{}\">{}</a>".format(deal.url, deal.title)
        self.deal_name_label.setText(text)
        self.deal_name_label.setTextFormat(Qt.RichText)
        self.deal_name_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.deal_name_label.setOpenExternalLinks(True)

        self.deal_price_edit.setText(str(round(deal.full_price, 3)))

        for i, component in enumerate(self.deal_current.get_components()):
            if i >= len(self.deal_components):
                print('Couldnt load every components')
                break
            comp_category, comp_name, comp_num = self.deal_components[i]
            comp_category.setCurrentIndex(component.component_base.category)
            comp_num.setText('1')
            comp_name.setText(component.component_base.name)
