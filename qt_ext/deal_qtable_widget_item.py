from datetime import datetime

from PyQt5.QtWidgets import QTableWidgetItem

from global_vars import date_format


class DealQTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other: QTableWidgetItem) -> bool:  # ['Id', 'Type', 'Title', 'Value N', 'Benef N', 'Value U', 'Benef U', 'Price', 'Date', 'Website']
        if 3 <= other.column() <= 7:  # Value N to Price
            try:
                return float(self.text()) < float(other.text())
            except:
                pass
        elif other.column() == 8:  # Date
            try:
                return datetime.strptime(self.text(), '%d-%m-%y %H:%M') < datetime.strptime(other.text(), '%d-%m-%y %H:%M')
            except:
                pass
        return QTableWidgetItem.__lt__(self, other)
