from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *
from prairie.view.chart_view import Chart, ChartView
import numpy as np
import yaml
import prairie.resources.configuration

try:
    # Standard library since Python 3.7
    from importlib import resources
except ImportError:
    # Try backport for Python < 3.7
    import importlib_resources as resources   # pip install importlib_resources

with resources.open_text(prairie.resources.configuration, 'conf.yml') as f:
    config_doc = yaml.load(f)
    config_doc = config_doc[config_doc['os']]


class BlockView(QGraphicsItemGroup):
    N = 6

    S_SIZE = [100, 80]
    M_SIZE = [150, 100]
    L_SIZE = [200, 150]

    INACTIVE_COLOR = [170, 170, 170, 255]
    ACTIVE_COLOR = [84, 179, 235, 255]
    ERROR_COLOR = [221, 182, 104, 255]

    NODES_IN_POSITIONS = [[3 / N],
                          [4 / N, 2 / N],
                          [1 / N, 3 / N, 5 / N],
                          [1 / N, 2 / N, 4 / N, 5 / N],
                          [1 / N, 2 / N, 3 / N, 4 / N, 5 / N]]

    def __init__(self, name='block_name', position=None, parent=None, size=None, block_id=None, preview=False):

        super(BlockView, self).__init__(parent)

        if size is not None:
            self.HEIGHT = size[1]
            self.WIDTH = size[0]
        else:
            self.HEIGHT = 140
            self.WIDTH = 90

        self.INTER = 10
        self.NODE_H = 18
        self.NODE_W = 11

        if isinstance(position, list):
            self._position = QPoint(*position)
        else:
            self._position = QPoint(0, 0)

        self.height = self.HEIGHT
        self.width = self.WIDTH

        self._nodes = []

        self.name = name
        self.type = 'neutral'

        self.id = block_id
        self._preview = preview

        if preview:
            self.preview = True

        self._state = 'neutral'

        self.block = QGraphicsRectItem()
        self.rect = self.boundingRect()
        self.create_block_and_flags()
        self.block_name = QGraphicsTextItem()
        self.set_block_name(name)

    @property
    def nodes(self):
        return {node.name: node for node in self._nodes}

    def nodes_in(self):
        return {node.name: node for node in self._nodes if node.type == 'in'}

    def nodes_out(self):
        return {node.name: node for node in self._nodes if node.type == 'out'}

    @property
    def position(self):
        return [self._position.x(), self._position.y()]

    @position.setter
    def position(self, position: list):
        self._position = QPoint(*position)

    @property
    def preview(self):
        return self._preview

    @preview.setter
    def preview(self, is_preview):
        if is_preview:
            self.setOpacity(0.5)
            self.setPos(self.mapToParent(QPoint(0,0)))
        self._preview = is_preview

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state
        self.color()

    def remove_connections(self):
        for node in self._nodes:
            for wire in node.wires:
                self.scene().removeItem(wire)
            node.wires = []
            node.set_connected(False, 0)

    def block_rect(self):
        return QRectF(self._position.x() + self.INTER, self._position.y() + 2 * self.INTER, self.width, self.height)

    def boundingRect(self):
        return QRectF(self._position.x(), self._position.y(), self.width + 2 * self.INTER, self.height + 2 * self.INTER)

    def create_nodes(self, nodes_dict, node_type, special=False, no_name=False, visible=True):

        block_rect = self.block_rect().getCoords()

        x = 0
        y = 1

        if node_type == 'out':
            x = 2
            y = 1

        for i, node_info in enumerate(nodes_dict[node_type].items()):

            if not special:
                pos = self.NODES_IN_POSITIONS[len(nodes_dict[node_type]) - 1][i]
            else:
                pos = 1 / self.height * (i + 1) * self.INTER + ((i + 1) * self.INTER / 2) / self.height

            node = NodeView(QRectF(block_rect[x] - self.NODE_W / 2,
                                   block_rect[y] + pos *
                                   self.height - self.NODE_H / 2,
                                   self.NODE_W, self.NODE_H),
                            name=node_info[0], type=node_type, block=self, node_id=node_info[1])

            node.setZValue(1)
            self.addToGroup(NodeGroupView(node, no_name=no_name, visible=visible))
            self._nodes.append(node)

    def hoverLeaveEvent(self, *args, **kwargs):
        for node in self._nodes:
            node.highlight(False)

    def set_size(self, width, height):
        self.width = width
        self.height = height
        self.block.setRect(self.block_rect())
        self.rect = self.boundingRect()
        self.update()

    def create_block_and_flags(self):
        self.block.setRect(self.block_rect())
        self.block.setZValue(3)
        self.color()
        self.addToGroup(self.block)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        # self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setZValue(2)
        # self.block.setOpacity(0.7)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

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

        if boolean:
            self.state = 'selected'
        else:
            self.state = 'neutral'

        self.color()

    def thread_start(self):
        self.state = 'running'

    def thread_done(self, output):
        self.state = 'neutral'

    def thread_error(self, executed):
        if executed:
            self.state = 'neutral'
        else:
            self.state = 'error'

    def to_pixmap(self) -> QPixmap:

        rect = self.boundingRect().toRect()

        if rect.isNull() and not rect.isValid():
            return QPixmap()

        pixmap = QPixmap(rect.size())
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.translate(rect.topLeft())
        self.paint(painter, None, None)
        #
        # for child in self.childItems():
        #     painter.save()
        #     painter.translate(child.mapToParent(self.pos()))
        #     child.paint(painter, None)
        #     painter.restore()

        painter.end()

        return pixmap

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.preview:
            self.setPos(self.mapToParent(event.pos()))
        else:
            return super(BlockView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self.preview:
            self.ungrabMouse()
        else:
            return super(BlockView, self).mouseReleaseEvent(event)

    def center(self):
        return self.scenePos() + self.rect.center()

    def color(self):
        if self.state == 'running':
            pen_color = QColor(*self.ACTIVE_COLOR)
        elif self.state == 'error':
            pen_color = QColor(*self.ERROR_COLOR)
        elif self.state == 'selected':
            pen_color = QColor(*self.INACTIVE_COLOR).darker(170)
        else:
            pen_color = QColor(*self.INACTIVE_COLOR)

        if self.state in ['neutral', 'selected']:
            brush_color = pen_color.lighter(300)
        else:
            brush_color = pen_color.lighter(160)

        brush_color.setAlpha(200)
        pen = QPen(pen_color)
        pen.setWidth(2)
        self.block.setPen(pen)
        self.block.setBrush(QBrush(brush_color, style=Qt.SolidPattern))

        return pen_color, brush_color


class NodeView(QGraphicsPolygonItem):

    def __init__(self, rect, value=None, name=None, type=None, block=None, parent=None, node_id=None):

        super(NodeView, self).__init__(parent=parent)

        # User interface attributes
        self.setPolygon(QPolygonF([QPointF(rect.x(), rect.y() + rect.height() * 0.2),
                                   QPointF(rect.x() + rect.width() / 2, rect.y()),
                                   QPointF(rect.x() + rect.width(), rect.y() + rect.height() * 0.2),
                                   QPointF(rect.x() + rect.width(), rect.y() + rect.height() * 0.8),
                                   QPointF(rect.x() + rect.width() / 2, rect.y() + rect.height()),
                                   QPointF(rect.x(), rect.y() + rect.height() * 0.8)]))
        self._rect = rect
        self.color = [185, 185, 185]
        self.color_highlight = [120, 120, 120]
        self.set_flags()

        self.id = node_id

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

    def rect(self):
        return self._rect

    def center(self):
        return self.scenePos() + self._rect.center()

    def highlight(self, boolean):
        if boolean:
            self.setBrush(QBrush(self.color_highlight, style=Qt.SolidPattern))
        else:
            self.setBrush(QBrush(self.color, style=Qt.SolidPattern))

    def set_colors(self, color, color_h):
        self.color = QColor(color[0], color[1], color[2])
        self.color_highlight = QColor(color_h[0], color_h[1], color_h[2])
        self.highlight(False)

    def set_flags(self):
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.set_colors(self.color, self.color_highlight)
        self.setPen(Qt.transparent)

    def ready(self):
        return self.ready

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        super(NodeView, self).paint(painter, option, widget)


class NodeGroupView(QGraphicsItemGroup):

    def __init__(self, node, parent=None, no_name=False, visible=True):

        super(NodeGroupView, self).__init__(parent)

        self.node = node

        self.addToGroup(node)
        self.node_name = QGraphicsTextItem()

        if not no_name:
            self.set_node_name()

        if not visible:
            self.hide()

    def set_node_name(self):
        if self.node.type == 'in':
            self.node_name.setPos(self.node._rect.x() + 12, self.node._rect.y() - 1)
        elif self.node.type == 'out':
            self.node_name.setPos(self.node._rect.x() - (12 + len(self.node.name) * 4), self.node._rect.y() - 1)
        self.node_name.setZValue(5000)
        self.node_name.setPlainText(self.node.name)
        font = QFont(config_doc['fonts']['node_name_font']['font_family'],
                     pointSize=config_doc['fonts']['node_name_font']['font_size'])

        font.setLetterSpacing(1, 0)
        self.node_name.setFont(font)
        self.node_name.setDefaultTextColor(QColor(180, 180, 180))
        self.node.block.addToGroup(self.node_name)


class LineEdit(QLineEdit):
    def __init__(self, txt, parent=None):
        super(LineEdit, self).__init__(txt, parent=parent)
        self.setStyleSheet("QLineEdit {border: 1px solid rgb(192, 192, 192); color: rgb(150, 150, 150)}")
        font = QFont(config_doc['fonts']['input_block_widget_font']['font_family'],
                     pointSize=config_doc['fonts']['input_block_widget_font']['font_size'])
        font.setLetterSpacing(1, 0.5)
        self.setFont(font)


class InputBlockView(BlockView):

    def __init__(self, name, nodes_dict, value=0, position=None, block_id=None, preview=False, view=None):

        super(InputBlockView, self).__init__(name=name, parent=None, position=position, size=[120, 30],
                                             block_id=block_id, preview=preview)

        self.value = value
        self.name = name
        self.type = 'input'
        self.size = [120, 30]

        # Widget setup
        self.widget = LineEdit(str(self.value))
        self.widget_proxy = QGraphicsProxyWidget(self.block)
        self.widget_proxy.setFocusPolicy(Qt.StrongFocus)
        self.widget_proxy.setWidget(self.widget)
        self.widget_proxy.setGeometry(QRectF(15, self.INTER + 15, self.size[0] - 40, self.size[1] - 10))
        self.widget.editingFinished.connect(self.get_value_field)
        self.widget.setReadOnly(True)

        self.create_nodes(nodes_dict, 'in', no_name=True, visible=False)
        self.create_nodes(nodes_dict, 'out', no_name=True)

        self.set_input(value)

        self.view = view

        # self.get_value_field()

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
            return super(InputBlockView, self).mouseMoveEvent(event)

    # Override
    def mouseDoubleClickEvent(self, event):
        if self.widget_proxy.isUnderMouse():
            self.widget.setReadOnly(False)
            new_event = QMouseEvent(event.type(), event.pos() - self.widget.pos(), event.button(), event.buttons(),
                                    event.modifiers())
            self.widget.mouseDoubleClickEvent(new_event)
        else:
            return super(InputBlockView, self).mouseDoubleClickEvent(event)

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
        self.value = self.widget.text()

        if self.view is not None:
            self.view.update_node_value(self.id, self.nodes_in()['x'].id, self.value)

    def set_input(self, value):
        self.widget.setText(str(value))

    def update_name_from_connection(self):
        new_name = self.view.get_connected_node_name(self.id, self.nodes_out()['x'].id)
        self.block_name.setPlainText(new_name)


class OutputBlockView(BlockView):

    def __init__(self, name, nodes_dict, position=-1, parent=None, block_id=None, preview=False):
        super(OutputBlockView, self).__init__(name=name, parent=parent, position=position, size=[150, 30],
                                              block_id=block_id, preview=preview)

        self.value = 0
        self.name = name
        self.type = 'output'

        self.value_text = QGraphicsTextItem()
        self.set_inside_value_text()

        self.create_nodes(nodes_dict, 'in', no_name=True)
        self.create_nodes(nodes_dict, 'out', no_name=True)

    def set_inside_value_text(self):
        self.value_text.setPos(15, 15 + self.INTER)
        self.value_text.setZValue(4)
        self.value_text.setPlainText(str(self.value))
        font = QFont('Roboto', pointSize=config_doc['fonts']['input_block_widget_font']['font_size'])
        font.setLetterSpacing(1, 0.5)
        self.value_text.setFont(QFont(font))
        self.value_text.setDefaultTextColor(QColor(150, 150, 150))
        self.addToGroup(self.value_text)

    def set_text(self, output):
        self.value_text.setPlainText(str(output))

    def thread_done(self, output):
        self.set_text(str(output[0]))
        super(OutputBlockView, self).thread_done(output)


class FunctionBlockView(BlockView):

    def __init__(self, function_name, nodes_dict, position=-1, parent=None, block_id=None, preview=False):
        super(FunctionBlockView, self).__init__(name=function_name, parent=parent, position=position, size=[130, 80],
                                                block_id=block_id, preview=preview)

        self.type = 'function'

        self.create_nodes(nodes_dict, 'in')
        self.create_nodes(nodes_dict, 'out')


class ChartBlockView(BlockView):

    def __init__(self, name, nodes_dict, position=-1, parent=None, block_id=None, preview=False):

        super(ChartBlockView, self).__init__(name=name, parent=parent, position=position, size=[300, 300],
                                             block_id=block_id, preview=preview)

        self.ncurves = 0
        self.value = 0
        self.name = name

        self.type = 'chart'

        self.chart = Chart()
        self.chart.legend().hide()
        npoints = 10000
        self.widget = ChartView(self.chart)
        self.widget.setRenderHint(QPainter.Antialiasing)
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setMargins(QMargins(15, 10, 10, 15))
        self.chart.setBackgroundRoundness(0)

        self.widget_proxy = QGraphicsProxyWidget(self.block)
        self.widget_proxy.setFocusPolicy(Qt.ClickFocus)
        self.widget_proxy.setWidget(self.widget)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

        self.widget_proxy.setGeometry(QRectF(15, self.INTER + 15, self.WIDTH - 10, self.HEIGHT - 10))
        
        self.chart.createDefaultAxes()
        self.chart.addSeries(QLineSeries())

        self.set_block_name(name)

        self.create_nodes(nodes_dict, 'in')
        self.create_nodes(nodes_dict, 'out')

    def add_data(self, xdata, ydata, color=QColor(84, 179, 235)):
        curve = QLineSeries()
        pen = curve.pen()
        if color is not None:
            pen.setColor(color)
        pen.setWidthF(1)
        curve.setPen(pen)
        # curve.setUseOpenGL(True)
        curve.append(self.series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)
        self.chart.createDefaultAxes()
        axes = self.chart.axes()
        for ax in axes:
            ax.setLabelsFont(QFont('Robotto', pointSize=9))
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
        for serie in self.chart.series():
            self.chart.removeSeries(serie)
            self.chart.update()
        self.add_data(self.nodes_in()['x'].value, self.nodes_in()['y'].value)

    def thread_done(self, output):
        for serie in self.chart.series():
            self.chart.removeSeries(serie)
        self.add_data(output[0], output[1])
        super(ChartBlockView, self).thread_done(output)
