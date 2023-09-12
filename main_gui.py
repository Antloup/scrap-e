import logging
import pickle
import time
from os import path
import sys
from typing import List

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QMainWindow, QGroupBox, \
    QGridLayout, QTabWidget
from qt_widgets.db_widget import DbWidget
from qt_widgets.deal_widget import DealWidget
from qt_widgets.labeler_widget import LabelerWidget
from qt_widgets.scraper_widget import ScraperWidget
from PyQt5.QtCore import Qt

variables_filename = 'variables.pkl'
SEPARATOR_CHARACTER = ';'


class GuiMainWindow(QMainWindow):

    max_width_column_1 = 350

    def __init__(self):
        super().__init__()

        self.window_layout = QGridLayout()
        self.deal_widget = DealWidget()
        self.scraper_widget = ScraperWidget()
        self.tab_widget = QTabWidget()
        self.labeler_widget = LabelerWidget()
        self.labeler_widget.update.connect(self.deal_widget.deal_refresh_data)
        self.db_widget = DbWidget()
        self.db_widget.update.connect(self.deal_widget.deal_refresh_data)

        # Variables box properties
        self.variables_group_box = QGroupBox('Variables')
        self.variables_update_button = QPushButton('Update')

        # Init boxes / window
        self.init_deal_box()
        self.init_scraper_widget()
        self.init_variables_box()
        self.init_database_box()
        self.init_labeler_widget()
        self.init_window()

        self.window_layout.addWidget(self.tab_widget, 0, 1, 3, 1)

    def init_window(self):
        window = QWidget()
        window.setLayout(self.window_layout)
        self.setCentralWidget(window)
        self.statusBar()
        self.setGeometry(300, 300, 750, 350)
        self.setWindowTitle('Deal value')
        self.show()

    def init_deal_box(self):
        self.deal_widget.setMaximumWidth(self.max_width_column_1)
        self.window_layout.addWidget(self.deal_widget, 0, 0)

    def init_scraper_widget(self):
        self.scraper_widget.setMaximumWidth(self.max_width_column_1)
        self.window_layout.addWidget(self.scraper_widget, 1, 0)

    def init_variables_box(self):
        main_layout = QVBoxLayout()
        self.variables_group_box.setLayout(main_layout)
        self.variables_group_box.setMaximumWidth(self.max_width_column_1)
        self.window_layout.addWidget(self.variables_group_box, 2, 0)

        line_layout = QHBoxLayout()

        self.variables_update_button.clicked.connect(self.db_widget.update_config)
        line_layout.addWidget(self.variables_update_button)

        main_layout.addLayout(line_layout)

    def init_database_box(self):
        self.tab_widget.addTab(self.db_widget, "DB")

    def init_labeler_widget(self):
        self.tab_widget.addTab(self.labeler_widget, "Labeler")

    def variables_combo_box_changed(self, value=0):
        var: str = self.variables_combo_box.currentText()
        if type(self.variables[var]) is list:
            if self.variables[var] == [None]:
                text = 'NONE'
            else:
                text = SEPARATOR_CHARACTER.join(self.variables[var])
        else:
            text = str(self.variables[var])
        self.variables_edit.setText(text)

    def save_variables(self):
        var: str = self.variables_combo_box.currentText()
        if self.variables_list[var] is List:
            self.variables[var] = self.variables_edit.text().split(SEPARATOR_CHARACTER)
            for i, v in enumerate(self.variables[var]):
                if v == 'NONE':
                    self.variables[var][i] = None
        elif self.variables_list[var] is str:
            self.variables[var] = self.variables_edit.text()
        elif self.variables_list[var] is int:
            try:
                self.variables[var] = int(self.variables_edit.text())
            except:
                self.variables[var] = 0
        elif self.variables_list[var] is float:
            try:
                self.variables[var] = float(self.variables_edit.text())
            except:
                self.variables[var] = 0.0
        with open(variables_filename, 'wb') as wvf:
            pickle.dump(self.variables, wvf)


if __name__ == "__main__":
    # logging.basicConfig(level='INFO')
    app = QApplication(sys.argv)
    # app.focusChanged.connect(lambda x,y: print(x,y))
    gui = GuiMainWindow()
    sys.exit(app.exec_())

