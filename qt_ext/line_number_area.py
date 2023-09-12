from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPaintEvent
from PyQt5.QtWidgets import QWidget
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from qt_ext.code_editor import CodeEditor

# WIP
class LineNumberArea(QWidget):

    def __init__(self, code_editor):  # CodeEditor
        super().__init__()
        self.code_editor = code_editor  # CodeEditor

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event:QPaintEvent):
        self.code_editor.lineNumberAreaPaintEvent(event)
