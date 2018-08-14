from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from model.compiler import functions

import os
import json


def path_to_dict(path):
    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path, x)) for x in os.listdir(path)]
    elif path.endswith('.py'):
        d['type'] = "file"
        functions_dict = functions(path)
        d['functions'] = [_function + '(' + ",".join(functions_dict[_function]['args']) + ')'
                          for _function in list(functions_dict.keys())]
    return d


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 drag and drop - pythonspot.com'
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 60

        self.tree = Tree('files/scripts')

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setCentralWidget(self.tree)

        self.show()

    @pyqtSlot()
    def on_click(self):
        print('PyQt5 button click')


class Tree(QTreeWidget):

    def __init__(self, folder_path):
        super(Tree, self).__init__()

        self.folder_path = folder_path

        self.parent_item = TreeItem(self.folder_path)
        self.insertTopLevelItem(0, self.parent_item)

        self.setDragEnabled(True)
        self.setAcceptDrops(False)

        self.header().hide()
        self.setStyleSheet('QTreeWidget {background: rgb(240,240,240); border: 0px}')

        self.setAttribute(Qt.WA_MacShowFocusRect, False)

        self.item = 0

    def mimeData(self, items):
        mime_datas = []

        for item in items:
            if isinstance(item, TreeItem) and item.type == 'function':

                if item.function_name == 'input':

                    mime_dict = {'type': 'input',
                                 'value': 0,
                                 'name': 'input',
                                 'object': 'block'}

                elif item.function_name == 'output':

                    mime_dict = {'type': 'output',
                                 'name': 'output',
                                 'object': 'block'}

                elif item.function_name == 'chart':

                    mime_dict = {'type': 'chart',
                                 'name': 'output',
                                 'object': 'block'}

                else:

                    mime_dict = {'type': 'function',
                                 'script_file': item.function_path,
                                 'script_function': item.function_name,
                                 'object': 'block'}

                mime_data = QMimeData()
                mime_data.setText(json.dumps(mime_dict))
                mime_datas.append(mime_data)

            if len(mime_datas) > 0:
                return mime_datas[0]

    def mouseMoveEvent(self, event: QMouseEvent):
        drag = QDrag(self)
        drag.setMimeData(self.mimeData(self.selectedItems()))
        drag.setPixmap(QPixmap('resources/icons/function.png'))

        drag.exec()


class TreeItem(QTreeWidgetItem):

    def __init__(self, path):
        self.path = path.strip('/')
        self.name = path.strip('/').split('/')[-1]
        self.function_path = "/".join(self.path.split('/')[:-1])
        try:
            self.function_name = self.path.split('/')[-1].split('(')[0]
        except IndexError:
            print('Function name is strange')

        super(TreeItem, self).__init__([self.name])

        self.type = -1

        if os.path.isdir(self.path):
            self.type = 'folder'
            self.setIcon(0, QIcon('resources/icons/folder.png'))
        elif os.path.isfile(self.path) and self.path.endswith('.py'):
            self.type = 'file'
            self.setIcon(0, QIcon('resources/icons/file.png'))
        else:
            self.type = 'function'
            self.setIcon(0, QIcon('resources/icons/function.png'))

        self.add_children()

    def add_children(self):

        if self.type == 'folder':
            folders = os.listdir(self.path)
            child_items = [TreeItem(os.path.join(self.path, folder)) for folder in folders]
            self.insertChildren(0, child_items)
        elif self.type == 'file':
            functions_dict = functions(self.path)
            functions_names = sorted(list(functions_dict.keys()))
            child_items = [TreeItem(os.path.join(self.path, _function + '(' + ",".join(functions_dict[_function]['args']) + ')'))
                           for _function in functions_names]
            self.insertChildren(0, child_items)