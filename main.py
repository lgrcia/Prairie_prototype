import sys
from PyQt5.QtWidgets import *

from controller.controller import Controller
from view.prairie_view import PrairieView
from model.core import Prairie
from view.file_system_tree import Tree

import yaml

with open('resources/configuration/conf.yml') as f:
    config_doc = yaml.load(f)


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Lorelei'
        self.left = 10
        self.top = 10
        self.width = 1200
        self.height = 1200

        self.central_widget = QWidget()
        self.main_layout = QSplitter()

        self.prairie = Prairie()
        self.prairie_view = PrairieView()

        self.code_tabs = QTabWidget()
        self.code_tabs.setFixedWidth(273)

        # self.addToolBar(PrairieViewToolBar(self))

        self.controller = Controller(self.prairie, self.prairie_view)

        self.file_explorer = Tree('files/scripts')

        self.code_tabs.addTab(self.file_explorer, 'Files')
        self.code_tabs.addTab(QWidget(), 'Blocks')
        self.code_tabs.addTab(QWidget(), 'Code')

        self.main_layout.addWidget(self.code_tabs)
        self.main_layout.addWidget(self.prairie_view)

        # Main layout setting
        self.setCentralWidget(self.main_layout)

        if config_doc['os'] == 'Darwin':
            self.setUnifiedTitleAndToolBarOnMac(True)

        self.style_ui()

    def style_ui(self):

        self.main_layout.setContentsMargins(0, 0, 0, 0)
        with open('resources/stylesheets/splitter.txt', 'r') as f:
            self.main_layout.setStyleSheet(f.read())
        with open('resources/stylesheets/tabWidget.txt', 'r') as f:
            self.code_tabs.setStyleSheet(f.read())

    # def keyPressEvent(self, event):


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.showMaximized()
    ex.show()
    sys.exit(app.exec_())
