from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class Dialog(QDialog):

    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self.resize(300,200)

    def showEvent(self, event):
        geom = self.frameGeometry()
        geom.moveCenter(QCursor.pos())
        self.setGeometry(geom)
        super(Dialog, self).showEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            event.accept()
        else:
            super(Dialog, self).keyPressEvent(event)


class PrairieViewToolBar(QToolBar):

    def __init__(self, parent=None):

        super(PrairieViewToolBar, self).__init__(parent)

        self.parent = parent

        spacers = [QWidget(), QWidget(), QWidget()]

        for spacer in spacers:
            spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.addAction('script')
        self.addWidget(spacers[0])
        self.blocks_action = self.addAction('blocks')
        self.addWidget(spacers[1])
        self.addAction('navigate')
        self.addAction('edit')
        self.addWidget(spacers[2])
        self.addAction('run')

        self.blocks_action.triggered.connect(self.open_window)

    def open_window(self):
        widget = self.parent.B
        if widget.isVisible():
            self.parent.B.hide()
        else:
            self.parent.B.show()


class BlockMenu(QFrame):

    def __init__(self):
        super(BlockMenu, self).__init__(QPushButton('test'))

