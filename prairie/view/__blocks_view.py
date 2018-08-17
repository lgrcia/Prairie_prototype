from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import *
import numpy as np
# import lib.prairie as pr
import io
import uuid
import yaml
from matplotlib import colors

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT

with open('../resources/configuration/conf.yml') as f:
    config_doc = yaml.load(f)
    config_doc = config_doc[config_doc['os']]


class mplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=100)

        # self.compute_initial_figure()

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class PlotWidget(QWidget):
    PLOT_WIDTH = 3
    PLOT_HEIGHT = 3

    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent=None)

        self.main_widget = QWidget(self)

        self.setAttribute(Qt.WA_DeleteOnClose)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.plot = plot(self, width=self.PLOT_WIDTH, height=self.PLOT_HEIGHT, dpi=100)

        self.navi_toolbar = NavigationToolbar2QT(self.plot, parent)
        # main_layout.addWidget(self.navi_toolbar)

        main_layout.addWidget(self.plot)

        self.setLayout(main_layout)

        self.actualise_ax()

        imgdata = io.StringIO()
        self.plot.fig.savefig(imgdata, format='svg')
        imgdata.seek(0)
        xmlreader = QXmlStreamReader(imgdata.getvalue())
        self.renderer = QSvgRenderer(xmlreader)

    def paintEvent(self, event):
        p = QPainter()
        p.begin(self)
        self.renderer.render(p)
        p.end()

    def actualise_ax(self):
        # self.plot.fig.clear()
        self.plot.draw()


class plot(mplCanvas):
    """Simple canvas with a sine plot."""

    def __init__(self, parent, width, height, dpi):
        super(plot, self).__init__(parent, width, height, dpi)
        self.fig.clear()
        # pr.use()
        self.main_ax = self.fig.add_subplot(1, 1, 1)
        self.compute_initial_figure()

    def compute_initial_figure(self):
        self.main_ax.set_title('Matplotlib plotting test', loc='left')
        self.main_ax.set_xlabel('label x')
        self.main_ax.set_ylabel('label y')
        # self.main_ax .plot([0,1,2], [0,2,3])
        # pr.style(self.main_ax, ticks=False)
        self.fig.tight_layout()


class BlockView(QGraphicsItemGroup):
    N = 6

    S_SIZE = [100, 80]
    M_SIZE = [150, 100]
    L_SIZE = [200, 150]

    NODES_IN_POSITIONS = [[3 / N],
                          [4 / N, 2 / N],
                          [1 / N, 3 / N, 5 / N],
                          [1 / N, 2 / N, 4 / N, 5 / N],
                          [1 / N, 2 / N, 3 / N, 4 / N, 5 / N]]

    def __init__(self, name='block_name', nodes_dict={}, position=-1, parent=None, size=[140, 90]):

        super(BlockView, self).__init__(parent)

        self.HEIGHT = size[1]
        self.WIDTH = size[0]
        self.INTER = 10
        self.NODE_H = 18
        self.NODE_W = 11

        if position != -1:
            self.position = position
        else:
            self.position = QPointF(0, 0)

        self.height = self.HEIGHT
        self.width = self.WIDTH

        self.nodes = []
        self.rect = self.boundingRect()

        self.name = name
        self.type = 'neutral'
        self.create_block_and_flags()
        self.create_nodes()

        self.block_name = QGraphicsTextItem()
        self.set_block_name(name)

    def contextMenuEvent(self, event):

        menu = QMenu()
        quitAction = menu.addAction("delete")
        # print(event.pos(), self.mapToScene(event.pos()), self.pos())
        action = menu.exec_(self.scene().views()[0].mapToGlobal(
            self.scene().views()[0].mapFromScene(QPointF.toPoint(self.pos() + event.pos()))))
        if action == quitAction:
            self.remove_connections()
            self.scene().removeItem(self)

    def remove_connections(self):
        for node in self.nodes:
            for wire in node.wires:
                self.scene().removeItem(wire)
            node.wires = []
            node.set_connected(False, 0)

    def block_rect(self):
        return QRectF(self.position.x() + self.INTER, self.position.y() + 2 * self.INTER, self.width, self.height)

    def boundingRect(self):
        return QRectF(self.position.x(), self.position.y(), self.width + 2 * self.INTER, self.height + 2 * self.INTER)

    def create_nodes(self):

        block_rect = self.block_rect().getCoords()

        if _function is not None:
            pass
            # implement the function signature gathering and input/output numbers + nodes creation
            function_name = _function[0]
            file_name = _function[1]

            function_dict = functions(file_name)[function_name]

            # print(function_dict)

            # For now let's try only args

            self.create_nodes(name=function_dict['args'], _type='in')
            self.create_nodes(name=function_dict['returns'], _type='out')

        elif _type is not None:

            if _type == 'in':
                x = 0
                y = 1
            elif _type == 'out':
                x = 2
                y = 1

            if isinstance(name, list):
                n = len(name)

            for i in np.arange(0, n):

                if isinstance(name, list):
                    _name = name[i]
                else:
                    _name = name

                if not special:
                    pos = self.NODES_IN_POSITIONS[n - 1][i]
                else:
                    pos = 1 / self.height * (i + 1) * self.INTER + ((i + 1) * self.INTER / 2) / self.height

                node = Node(QRectF(block_rect[x] - self.NODE_W / 2,
                                   block_rect[y] + pos *
                                   self.height - self.NODE_H / 2,
                                   self.NODE_W, self.NODE_H), value=value, name=_name, type=_type, block=self)

                node.setZValue(1)
                self.addToGroup(Node_Group(node))
                self.nodes.append(node)

        else:
            pass

    def notify_connected_blocks(self):
        for node in self.get_nodes_out():
            node.notify_connected_blocks()

    def hoverLeaveEvent(self, *args, **kwargs):
        for node in self.nodes:
            node.highlight(False)

    def set_size(self, width, height):
        self.width = width
        self.height = height
        self.block.setRect(self.block_rect())
        self.rect = self.boundingRect()
        self.update()

    def all_node_connected(self):
        return len(self.nodes) == len(self.get_connected_nodes())

    def get_nodes_in(self):
        return [node for node in self.nodes if node.type == 'in']

    def get_nodes_out(self):
        return [node for node in self.nodes if node.type == 'out']

    def get_connected_nodes(self):
        return [node for node in self.nodes if node.is_connected()]

    def create_block_and_flags(self):
        self.block = QGraphicsRectItem(self.block_rect())
        self.block.setZValue(3)
        self.block.setBrush(QBrush(QColor(255, 255, 255, 200), style=Qt.SolidPattern))
        pen = QPen(QColor(192, 192, 192))
        pen.setWidth(2)
        self.block.setPen(pen)
        self.addToGroup(self.block)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setZValue(2)
        # self.block.setOpacity(0.7)

    def set_position(self, position):
        self.position = position

    def notify(self):
        if len([node for node in self.get_nodes_in() if node.ready]) == len(self.get_nodes_in()) and len(
                self.get_nodes_in()) != 0:
            self.thread.start()

    def describe(self):
        print('######  Block ', self.name, ' type ', self.type)
        # for node in self.get_nodes_in():
        #     print('Node ', node.name, 'from', node.block.name,
        #           ', type: ', node.type,
        #           ', connected: ', node.is_connected,
        #           ' to: ', [str(n.name) + ' from ' + str(n.block.name) for n in node.connected_to],
        #           ', value: ', node.value,
        #           ', ready: ', node.ready)

        for node in self.get_nodes_out():
            print('Node ', node.name, 'from', node.block.name,
                  ', type: ', node.type,
                  ', connected: ', node.is_connected,
                  ' to: ', [str(n.name) + ' from ' + str(n.block.name) for n in node.connected_to],
                  ', value: ', node.value,
                  ', ready: ', node.ready, '\n')

    def get_node(self, name):
        for node in self.nodes:
            if node.name == name:
                return node
        return -1

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        if option == QStyle.State_Selected:
            option = QStyle.State_None
        # super(Block, self).paint(painter, option, widget)

    def set_block_name(self, name):
        self.block_name.setPos(7, 0)
        self.block_name.setZValue(4)
        self.block_name.setPlainText(name)
        font = QFont(config_doc['fonts']['block_name_font']['font_family'],
                     pointSize=config_doc['fonts']['block_name_font']['font_size'])

        font.setLetterSpacing(1, 0)
        self.block_name.setFont(font)
        self.block_name.setDefaultTextColor(QColor(80, 80, 80))
        self.addToGroup(self.block_name)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            self.highlight(not self.isSelected())

        return super(BlockView, self).itemChange(change, value)

    def highlight(self, boolean):

        pen_color = QColor(192, 192, 192)

        if boolean:
            pen_color = QColor(130, 130, 130)

        pen = QPen(pen_color)
        pen.setWidth(2)
        self.block.setPen(pen)


class Node(QGraphicsPolygonItem):

    def __init__(self, rect, value=None, name=None, type=None, block=None, parent=None, wire=None):

        super(Node, self).__init__(parent=parent)

        # User interface attributes
        self.setPolygon(QPolygonF([QPointF(rect.x(), rect.y() + rect.height() * 0.2),
                                   QPointF(rect.x() + rect.width() / 2, rect.y()),
                                   QPointF(rect.x() + rect.width(), rect.y() + rect.height() * 0.2),
                                   QPointF(rect.x() + rect.width(), rect.y() + rect.height() * 0.8),
                                   QPointF(rect.x() + rect.width() / 2, rect.y() + rect.height()),
                                   QPointF(rect.x(), rect.y() + rect.height() * 0.8)]))
        self.rect = rect
        self.color = [185, 185, 185]
        self.color_highlight = [120, 120, 120]
        self.set_flags()
        self.id = uuid.uuid4()

        self.initial_value = value

        # Variable attributes
        self.value = value
        self.name = name
        self.type = type

        # Block object attributes
        self.block = block
        self.ready = False
        self.connected = False
        self.connected_to = []

        self.wires = []

        if isinstance(name, str):
            self.setToolTip(self.name)

    def set_node_type(self, node_type):
        self.type = node_type

    def is_connected(self):
        return self.connected

    def set_connected(self, boolean, connected_object):
        self.connected = boolean
        if boolean:
            self.connected_to.append(connected_object)
        else:
            self.connected_to = []
            self.ready = False

    def highlight(self, boolean):
        if boolean:
            self.setBrush(QBrush(self.color_highlight, style=Qt.SolidPattern))
        else:
            self.setBrush(QBrush(self.color, style=Qt.SolidPattern))

    def set_colors(self, color, color_h):
        self.color = QColor(color[0], color[1], color[2])
        self.color_highlight = QColor(color_h[0], color_h[1], color_h[2])
        self.highlight(False)

    def set_variable(self, value, name=None):
        self.value = value
        if name is not None:
            self.name = name

    def set_flags(self):
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.set_colors(self.color, self.color_highlight)
        self.setPen(Qt.transparent)

    def set_ready(self, ready):
        self.ready = ready

    def set_connected_node_ready(self, ready):
        for connected_node in self.connected_to:
            connected_node.set_ready(ready)

    def ready(self):
        return self.ready

    def notify_connected_blocks(self):
        for connected_node in self.connected_to:
            connected_node.notify_block()

    def notify_block(self):
        self.block.notify()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        super(Node, self).paint(painter, option, widget)

    def add_wire(self, wire):
        self.wires.append(wire)

    def reset(self):
        self.ready = False
        self.value = self.initial_value


class Node_Group(QGraphicsItemGroup):

    def __init__(self, node, parent=None):

        super(Node_Group, self).__init__(parent)

        self.node = node

        self.addToGroup(node)
        self.node_name = QGraphicsTextItem()

        if node.type == 'in':
            self.set_node_name()

    def set_node_name(self):
        if self.node.type == 'in':
            self.node_name.setPos(self.node.rect.x() + 12, self.node.rect.y() - 1)
        self.node_name.setZValue(5000)
        self.node_name.setPlainText(self.node.name)
        font = QFont(config_doc['fonts']['node_name_font']['font_family'],
                     pointSize=config_doc['fonts']['node_name_font']['font_size'])

        font.setLetterSpacing(1, 0)
        self.node_name.setFont(font)
        self.node_name.setDefaultTextColor(QColor(180, 180, 180))
        self.node.block.addToGroup(self.node_name)


class BlockThread(QThread):
    notifyState = pyqtSignal(bool)
    notifyOutput = pyqtSignal(list)

    def __init__(self, function_name=None, function_file=None, args=[], kwargs=[], block=None, parent=None):

        super(BlockThread, self).__init__(parent)
        self.args = []
        self.kwargs = []
        self.output = []

        self.block = block
        self.function_name = function_name
        self.function_file = function_file
        self.function_attr = -1

        self.exec_import()
        self.set_arguments(args, kwargs)

    def exec_import(self):
        # dev : Check if already imported

        self.function_file = self.function_file.replace('/', '.')

        exec('import ' + self.function_file)
        self.function_attr = getattr(eval(self.function_file), self.function_name)

    def run(self):

        # Function call
        if len(self.args) == 0 and len(self.kwargs) == 0:
            self.output = self.function_attr()
        elif len(self.args) >= 1 and len(self.kwargs) == 0:
            self.output = self.function_attr(*self.args)
        elif len(self.args) == 0 and len(self.kwargs) >= 1:
            self.output = self.function_attr(**self.kwargs)
        elif len(self.args) > 1 and len(self.kwargs) >= 1:
            self.output = self.function_attr(*self.args, **self.kwargs)

        if not isinstance(self.output, tuple):
            self.output = [self.output]

        self.set_out_nodes_variables()
        print('\n', self.block.name, 'ready', '\n')

        self.quit()

    def set_arguments(self, args=[], kwargs=[]):
        self.args = args
        self.kwargs = kwargs

    def set_out_nodes_variables(self):
        # Set the out nodes variables from the thread output
        nodes_out = [node for node in self.block.get_nodes_out()]
        for i, node in enumerate(nodes_out):
            if self.output is not None:
                node.set_variable(value=self.output[i])
                for connected_node in node.connected_to:
                    connected_node.set_variable(value=self.output[i])
            node.set_ready(True)
            node.set_connected_node_ready(True)
            node.notify_connected_blocks()


class LineEdit(QLineEdit):
    def __init__(self, txt, parent=None):
        super(LineEdit, self).__init__(txt, parent=parent)
        self.setStyleSheet("QLineEdit {border: 1px solid rgb(192, 192, 192); color: rgb(150, 150, 150)}")
        font = QFont(config_doc['fonts']['input_block_widget_font']['font_family'],
                     pointSize=config_doc['fonts']['input_block_widget_font']['font_size'])
        font.setLetterSpacing(1, 0.5)
        self.setFont(font)


class InputBlock(BlockView):

    def __init__(self, name='input', value=0, position=-1, parent=None, size=[120, 30]):

        self.set_position(position)
        super(InputBlock, self).__init__(name=name, parent=parent, position=position, size=size)

        self.value = value
        self.name = name
        self.type = 'input'

        # Widget setup
        self.widget = LineEdit(str(self.value))
        self.widget_proxy = QGraphicsProxyWidget(self.block)
        self.widget_proxy.setFocusPolicy(Qt.StrongFocus)
        self.widget_proxy.setWidget(self.widget)
        self.widget_proxy.setGeometry(QRectF(15, self.INTER + 15, size[0] - 40, size[1] - 10))
        self.widget.editingFinished.connect(self.get_value_field)
        self.widget.setReadOnly(True)

        self.create_nodes(_type='out', n=1, special=True)

        self.thread = BlockThread('binput', 'lscripts/basic_block_functions', block=self, args=[self.value])
        self.thread.finished.connect(self.notify_connected_blocks)

    def value(self):
        return self.value

    def start_thread(self):
        self.thread.start()

    def set_variable(self, value):
        self.value = value
        if isinstance(self.value, (int, float)):
            self.thread.set_arguments(args=[self.value])
        else:
            self.thread.set_arguments(args=[-1])

    # Override
    def mousePressEvent(self, event):
        if self.widget_proxy.isUnderMouse():
            self.widget.setReadOnly(False)
            self.widget.setFocus(0)
            new_event = QMouseEvent(event.type(), event.pos() - self.widget.pos(), event.button(), event.buttons(),
                                    event.modifiers())
            self.widget.mousePressEvent(new_event)

    # Override
    def mouseMoveEvent(self, event):
        if self.widget.hasFocus():
            new_event = QMouseEvent(event.type(), event.pos() - self.widget.pos(), event.button(), event.buttons(),
                                    event.modifiers())
            self.widget.mouseMoveEvent(new_event)
        else:
            return super(InputBlock, self).mouseMoveEvent(event)

    # Override
    def mouseDoubleClickEvent(self, event):
        if self.widget_proxy.isUnderMouse():
            self.widget.setReadOnly(False)
            new_event = QMouseEvent(event.type(), event.pos() - self.widget.pos(), event.button(), event.buttons(),
                                    event.modifiers())
            self.widget.mouseDoubleClickEvent(new_event)
        else:
            return super(InputBlock, self).mouseDoubleClickEvent(event)

    # Override
    def keyPressEvent(self, event):
        self.widget.keyPressEvent(event)
        if event.key() == Qt.Key_Return:
            self.focusOutEvent()

    # Override
    def focusOutEvent(self, *args, **kwargs):
        self.get_value_field()
        self.widget_proxy.clearFocus()
        self.widget.setReadOnly(True)

    def get_value_field(self):
        self.value = eval(self.widget.text())
        self.set_variable(value=self.value)


class OutputBlock(BlockView):

    def __init__(self, name='input', value=0, position=-1, parent=None):
        self.set_position(position)
        super(OutputBlock, self).__init__(name=name, parent=parent, position=position, size=[60, 30])

        self.value = value
        self.name = name
        self.type = 'output'

        self.value_text = QGraphicsTextItem()
        self.set_inside_value_text()

        self.create_nodes(_type='in', n=1)

        self.thread = BlockThread('boutput', 'lscripts/basic_block_functions', args=[self.value], block=self)
        self.thread.finished.connect(self.set_text_value)

    def value(self):
        return self.value

    def start_thread(self):
        self.thread.start()

    def set_inside_value_text(self):
        self.value_text.setPos(15, 15 + self.INTER)
        self.value_text.setZValue(4)
        self.value_text.setPlainText(str(self.value))
        font = QFont('Roboto', pointSize=8.5)
        font.setLetterSpacing(1, 0.5)
        self.value_text.setFont(QFont(font))
        self.value_text.setDefaultTextColor(QColor(150, 150, 150))
        self.addToGroup(self.value_text)

    def get_node_value(self):
        return self.nodes[0].value

    def set_text_value(self):
        self.value = self.get_node_value()
        self.value_text.setPlainText(str(self.value))


class FunctionBlock(BlockView):

    def __init__(self, function_name, file_name, position=-1, parent=None, size=[130, 80]):
        self.set_position(position)
        super(FunctionBlock, self).__init__(name=function_name, parent=parent, position=position, size=size)

        self.function_name = function_name
        self.file_name = file_name
        self.type = 'function'

        self.create_nodes(_function=[self.function_name, self.file_name])

        self.thread = BlockThread(self.function_name, self.file_name[0:len(self.file_name) - 3], block=self)
        self.thread.finished.connect(self.notify_connected_blocks)

    def value(self):
        return self.value

    def start_thread(self):
        self.thread.start()

    def get_nodes_in_value(self):
        return {node.name: node.value for node in self.get_nodes_in()}

    def nodes_in_value_dict_in_arg(self, nodes_in_value_dict):
        return [nodes_in_value_dict[name] for name in self.get_function_args()]

    # Overide
    def notify(self):
        if len([node for node in self.get_nodes_in() if node.ready]) == len(self.get_nodes_in()) and len(
                self.get_nodes_in()) != 0:
            self.thread.set_arguments(args=self.nodes_in_value_dict_in_arg(self.get_nodes_in_value()))
            self.thread.start()

    def get_function_args(self):
        return functions(self.file_name)[self.function_name]['args']


class ChartBlock(FunctionBlock):

    def __init__(self, name='input', position=-1, parent=None):

        self.set_position(position)
        super(FigureBlock, self).__init__(function_name='bdoubleinput', file_name='lscripts/basic_block_functions.py',
                                          parent=parent, position=position, size=[250, 200])

        self.ncurves = 0
        self.value = 0
        self.name = name

        self.type = 'chart'

        self.chart = Chart()
        self.chart.legend().hide()
        npoints = 10000
        xdata = np.linspace(0., 10., npoints)
        self.widget = ChartView(self.chart)
        self.widget.setRenderHint(QPainter.Antialiasing)
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setMargins(QMargins(3, 3, 3, 3))
        self.chart.setBackgroundRoundness(0)

        self.widget_proxy = QGraphicsProxyWidget(self.block)
        self.widget_proxy.setFocusPolicy(Qt.ClickFocus)
        self.widget_proxy.setWidget(self.widget)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        self.widget_proxy.setGeometry(QRectF(15, self.INTER + 15, self.WIDTH - 10, self.HEIGHT - 10))

        # self.set_title('testing plot AR4154')

        self.thread.finished.connect(self.update_graph)

        self.chart.createDefaultAxes()
        self.chart.addSeries(QLineSeries())

        self.set_block_name(name)

    def add_data(self, xdata, ydata, color=QColor(84, 179, 235)):
        curve = QLineSeries()
        pen = curve.pen()
        if color is not None:
            pen.setColor(color)
        pen.setWidthF(.5)
        curve.setPen(pen)
        # curve.setUseOpenGL(True)
        curve.append(self.series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)
        self.chart.createDefaultAxes()
        axes = self.chart.axes()
        for ax in axes:
            ax.setLabelsFont(QFont('Robotto', pointSize=6))
        self.ncurves += 1

    def series_to_polyline(self, xdata, ydata):
        """Convert series data to QPolygon(F) polyline

        This code is derived from PythonQwt's function named
        `qwt.plot_curve.series_to_polyline`"""
        size = len(xdata)
        polyline = QPolygonF(size)
        pointer = polyline.data()
        dtype, tinfo = np.float, np.finfo  # integers: = np.int, np.iinfo
        pointer.setsize(2 * polyline.size() * tinfo(dtype).dtype.itemsize)
        memory = np.frombuffer(pointer, dtype)
        memory[:(size - 1) * 2 + 1:2] = xdata
        memory[1:(size - 1) * 2 + 2:2] = ydata
        return polyline

    def set_title(self, title):
        self.chart.setTitle(title)

    def mousePressEvent(self, event):
        if self.widget_proxy.isUnderMouse():
            self.widget.setFocus(0)
            new_event = QMouseEvent(event.type(), event.pos() - self.widget.pos(), event.button(), event.buttons(),
                                    event.modifiers())
            self.widget.mousePressEvent(new_event)

    def wheelEvent(self, event):
        if self.widget_proxy.isUnderMouse():
            self.widget_proxy.wheelEvent(event)

    def keyPressEvent(self, event):
        self.widget.keyPressEvent(event)
        if event.key() == Qt.Key_Return:
            self.focusOutEvent()

    def update_graph(self, data=None):
        # print([node.value for node in self.nodes])
        self.add_data(self.nodes[0].value, self.nodes[1].value)


class ConsoleBlockOut(InputBlock):

    def __init__(self, name='input', value=0, position=-1, parent=None):
        super(ConsoleBlockOut, self).__init__(name=name, parent=parent, position=position, size=[200, 100], value=value)

        self.set_variable(eval(value))

        self.type = 'console_out'

        # self.widget = QPlainTextEdit()

        font = QFont(config_doc['fonts']['console_block_widget_font']['font_family'],
                     pointSize=config_doc['fonts']['console_block_widget_font']['font_size'])

        font.setBold(True)

        self.value = value
        self.text_value = ''

        self.widget_proxy.setGeometry(QRectF(15, self.INTER + 15, 200 - 10, 100 - 10))

        self.widget.setFont(font)

        self.widget.setAlignment(Qt.AlignTop)
        self.widget.setStyleSheet(
            "QLineEdit {border: 0px solid rgb(220, 220, 220); background-color: rgb(40, 40, 40); color: rgb(200,200,200)}")

    def set_variable(self, value):
        self.thread.set_arguments(args=[value])

    def get_value_field(self):
        self.text_value = self.widget.text()
        super(ConsoleBlockOut, self).get_value_field()


class ConsoleBlockIn(OutputBlock):

    def __init__(self, name='input', value=0, position=-1, parent=None):
        super(ConsoleBlockIn, self).__init__(name=name, parent=parent, position=position, size=[150, 100])

        self.widget.setAlignment(Qt.AlignTop)
        self.widget.setStyleSheet(
            "QLineEdit {border: 0px solid rgb(192, 192, 192); background-color: rgb(40, 40, 40); color: rgb(200,200,200)}")


class FigureBlock(FunctionBlock):

    def __init__(self, name='input', position=-1, parent=None):
        self.set_position(position)
        super(FigureBlock, self).__init__(function_name='bdoubleinput', file_name='lscripts/basic_block_functions.py',
                                          parent=parent, position=position, size=[350, 300])

        self.value = 0
        self.name = name
        self.type = 'figure'

        self.widget = PlotWidget()

        self.widget_proxy = QGraphicsProxyWidget(self.block)
        self.widget_proxy.setContentsMargins(0, 0, 0, 0)
        self.widget_proxy.setFocusPolicy(Qt.ClickFocus)
        self.widget_proxy.setWidget(self.widget)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        self.widget_proxy.setGeometry(QRectF(15, self.INTER + 15, self.WIDTH - 10, self.HEIGHT - 10))

        self.thread.finished.connect(self.update_graph)

        self.set_block_name(name)

    def update_graph(self, data=None):
        # print([node.value for node in self.nodes])
        self.widget.plot.main_ax.cla()
        self.widget.plot.main_ax.plot(self.nodes[0].value, self.nodes[1].value)
        self.widget.plot.draw()


class FigureBlock2(FunctionBlock):

    def __init__(self, name='input', position=-1, parent=None):
        self.set_position(position)
        super(FigureBlock, self).__init__(function_name='bdoubleinput', file_name='lscripts/basic_block_functions.py',
                                          parent=parent, position=position, size=[350, 300])

        self.value = 0
        self.name = name

        self.widget = MPLPlot()

        self.widget_proxy = QGraphicsProxyWidget(self.block)
        self.widget_proxy.setContentsMargins(0, 0, 0, 0)
        self.widget_proxy.setFocusPolicy(Qt.ClickFocus)
        self.widget_proxy.setWidget(self.widget)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        self.widget_proxy.setGeometry(QRectF(15, self.INTER + 15, self.WIDTH - 10, self.HEIGHT - 10))

        self.thread.finished.connect(self.update_graph)

        self.set_block_name(name)

    def update_graph(self, data=None):
        # print([node.value for node in self.nodes])
        self.widget.axes.cla()
        self.widget.axes.plot(self.nodes[0].value, self.nodes[1].value)
        self.widget.draw()


from matplotlib import pyplot as plt


class MPLPlot(QWidget):
    def __init__(self):
        super(MPLPlot, self).__init__()

        self.figure = Figure()
        self.axes = self.figure.gca()
        self.axes.set_title("Use the mouse wheel to zoom")
        self.axes = plt.plot(np.random.rand(50))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setGeometry(0, 0, 500, 500)

        imgdata = io.StringIO()
        self.figure.savefig(imgdata, format='svg')
        imgdata.seek(0)
        xmlreader = QXmlStreamReader(imgdata.getvalue())
        self.renderer = QSvgRenderer(xmlreader)

    def paintEvent(self, event):
        p = QPainter()
        p.begin(self)
        self.renderer.render(p)
        p.end()


class ImageBlock(FunctionBlock):

    def __init__(self, name='input', position=-1, parent=None):

        self.set_position(position)
        super(ImageBlock, self).__init__(function_name='binput', file_name='lscripts/basic_block_functions.py',
                                         parent=parent, position=position, size=[350, 300])

        self.value = 0
        self.name = name
        self.type = 'image'

        self.widget = PlotWidget()

        self.widget_proxy = QGraphicsProxyWidget(self.block)
        self.widget_proxy.setContentsMargins(0, 0, 0, 0)
        self.widget_proxy.setFocusPolicy(Qt.ClickFocus)
        self.widget_proxy.setWidget(self.widget)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        self.widget_proxy.setGeometry(QRectF(15, self.INTER + 15, self.WIDTH - 10, self.HEIGHT - 10))

        self.thread.finished.connect(self.update_graph)

        self.set_block_name(name)

    def update_graph(self, data=None):
        self.widget.plot.main_ax.cla()
        x = self.nodes[0].value
        self.widget.plot.main_ax.imshow(x)
        self.widget.plot.draw()
        self.widget.repaint()

    def contextMenuEvent(self, event):

        menu = QMenu()
        quitAction = menu.addAction("delete")
        menuAction = menu.addAction("plot parameters")
        # print(event.pos(), self.mapToScene(event.pos()), self.pos())
        action = menu.exec_(self.scene().views()[0].mapToGlobal(
            self.scene().views()[0].mapFromScene(QPointF.toPoint(self.pos() + event.pos()))))
        if action == quitAction:
            self.remove_connections()
            self.scene().removeItem(self)
        elif action == menuAction:
            self.widget.navi_toolbar.edit_parameters()


class _ImageBlock(FunctionBlock):

    def __init__(self, name='input', position=-1, parent=None):
        self.set_position(position)
        super(_ImageBlock, self).__init__(function_name='binput', file_name='lscripts/basic_block_functions.py',
                                          parent=parent, position=position, size=[350, 300])

        self.value = 0
        self.name = name
        self.widget = MPLPlot()
        self.widget_proxy = QGraphicsProxyWidget(self.block)
        self.widget_proxy.setContentsMargins(0, 0, 0, 0)
        self.widget_proxy.setFocusPolicy(Qt.ClickFocus)
        self.widget_proxy.setWidget(self.widget)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        self.widget_proxy.setGeometry(QRectF(15, self.INTER + 15, self.WIDTH - 10, self.HEIGHT - 10))

        self.thread.finished.connect(self.update_graph)

        self.set_block_name(name)

    def update_graph(self, data=None):
        self.widget.axes.cla()
        self.widget.axes.imshow(self.nodes[0].value)
        self.widget.canvas.draw()
        self.widget.repaint()
