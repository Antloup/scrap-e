from typing import List

from PyQt5.QtCore import QRect, Qt, qRound
from PyQt5.QtGui import QPaintEvent, QResizeEvent, QColor, QTextFormat, QPainter, QTextBlock
from PyQt5.QtWidgets import QPlainTextEdit, QWidget, QTextEdit

from qt_ext.line_number_area import LineNumberArea

# WIP
class CodeEditor(QPlainTextEdit):

    def __init__(self, parent: QWidget = None):
        super().__init__()
        self.parent = parent
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaPaintEvent(self, event: QPaintEvent):
        painter: QPainter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), Qt.yellow)

        block: QTextBlock = self.firstVisibleBlock()
        blockNumber: int = block.blockNumber()
        top: int = qRound(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom: int = top + qRound(self.blockBoundingRect(block).height())

        while (block.isValid() and top <= event.rect().bottom()):
            if (block.isVisible() and bottom >= event.rect().top()):
                number: str = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width(), self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + qRound(self.blockBoundingRect(block).height())
            blockNumber +=1


    def lineNumberAreaWidth(self) -> int:
        digits: int = 1
        maximum: int = max(1, self.blockCount())
        while (maximum >= 10):
            maximum /= 10
            digits += 1
        space: int = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def resizeEvent(self, event: QResizeEvent):
        QPlainTextEdit.resizeEvent(self, event)
        cr: QRect = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def updateLineNumberAreaWidth(self, newBlockCount: int):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine(self):
        extraSelections: List = []

        if (not self.isReadOnly()):
            selection = QTextEdit.ExtraSelection()

            lineColor = QColor(Qt.yellow).lighter(160)

            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def updateLineNumberArea(self, rect: QRect, dy: int):
        if (dy):
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

            if (rect.contains(self.viewport().rect())):
                self.updateLineNumberAreaWidth(0)
