from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from prairie.view.blocks_view import *
import json
import yaml

with open('resources/configuration/conf.yml') as f:
    config_doc = yaml.load(f)
    os = config_doc['os']
    config_doc = config_doc[config_doc['os']]


class ConnectionView(QGraphicsItemGroup):

    def __init__(self, node_in, node_out, scene, parent=None):

        QGraphicsItemGroup.__init__(self, parent)

        self.node_in = node_in
        self.node_out = node_out

        self.left_segment = QGraphicsLineItem(QLineF(0, 0, 0, 0))
        self.middle_segment = QGraphicsLineItem(QLineF(0, 0, 0, 0))
        self.right_segment = QGraphicsLineItem(QLineF(0, 0, 0, 0))

        self._valid = False

        self.set_lines(QColor(84, 179, 235))

        self.addToGroup(self.left_segment)
        self.addToGroup(self.middle_segment)
        self.addToGroup(self.right_segment)

        self.scene = scene

        self.scene.changed.connect(self.update_connection)

    def boundingRect(self):
        top_left_point = self.node_in.center()
        bottom_right_point = self.node_out.center()
        bounds = bottom_right_point - top_left_point
        size = QSizeF(bounds.x(), bounds.y())
        return QRectF(top_left_point, size)

    def contextMenuEvent(self, event):

        menu = QMenu()
        quit_action = menu.addAction("delete")
        point = self.scene.views()[0].mapFromScene(QPointF.toPoint(self.pos() + event.pos()))
        action = menu.exec_(self.scene.views()[0].mapToGlobal(point))
        if action == quit_action:
            self.scene.views()[0].remove_connection(self)

    def update_connection(self):
        a = 0
        b_rect = self.boundingRect().getCoords()
        mid_x = b_rect[0]+(b_rect[2]-b_rect[0])/2
        self.left_segment.setLine(b_rect[0], b_rect[1], mid_x - a, b_rect[1])
        self.middle_segment.setLine(mid_x - a, b_rect[1], mid_x + a, b_rect[3])
        self.right_segment.setLine(mid_x + a, b_rect[3], b_rect[2], b_rect[3])

    def set_lines(self, color):
        pen = QPen()
        pen.setWidth(2)
        pen.setBrush(color)
        self.left_segment.setPen(pen)
        self.middle_segment.setPen(pen)
        self.right_segment.setPen(pen)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        super(ConnectionView, self).paint(painter, option, widget)

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, valid):
        self._valid = valid

        if valid:
            self.set_lines(QColor(100, 100, 100))
        else:
            self.set_lines(QColor(185, 185, 185))


class EmptyItem(QGraphicsRectItem):

    def __init__(self, position):
        super(EmptyItem, self).__init__(0, 0, 1, 1)
        self.setPos(self.mapToParent(position))

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
            self.setPos(self.mapToParent(event.pos()))

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
            self.ungrabMouse()

    def dragMoveEvent(self, event: 'QGraphicsSceneDragDropEvent'):
            self.setPos(self.mapToParent(event.pos()))

    def center(self):
        return self.scenePos() + self.rect().center()


class PrairieView(QGraphicsView):

    def __init__(self, parent=None):

        super(PrairieView, self).__init__(parent)

        self._controller = None

        self._connection_creation_mode = False
        self._edit_mode = True
        self._navigate_mode = False
        self._multiple_selection_mode = False

        self.scene = QGraphicsScene()

        self.scene.setBackgroundBrush(QColor(255, 255, 255))

        self.setRenderHint(QPainter.Antialiasing)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.menu = QMenu()
        self.delete_a = QAction('delete')
        self.menu.addAction(self.delete_a)

        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.setScene(self.scene)

        self._last_item_clicked = None
        self._connection_preview_item = None
        self._connection_preview = None
        self._block_preview = None

        self.setAcceptDrops(True)
        self.setStyleSheet('QGraphicsView {border: 0px}')

    @property
    def edit_mode(self):
        return self._edit_mode

    @edit_mode.setter
    def edit_mode(self, edit_mode: bool):
        self._edit_mode = edit_mode
        self._navigate_mode = not edit_mode

    @property
    def navigate_mode(self):
        return self._navigate_mode

    @navigate_mode.setter
    def navigate_mode(self, navigate_mode: bool):
        self._edit_mode = navigate_mode
        self._navigate_mode = not navigate_mode

    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, controller):
        self._controller = controller

    @property
    def connection_creation_mode(self):
        return self._connection_creation_mode

    @connection_creation_mode.setter
    def connection_creation_mode(self, boolean):
        self._connection_creation_mode = boolean
        self.freeze_all_blocks(boolean)
        if boolean:
            self.setDragMode(QGraphicsView.NoDrag)

    @property
    def multiple_selection_mode(self):
        return self._multiple_selection_mode

    @multiple_selection_mode.setter
    def multiple_selection_mode(self, boolean):
        if boolean:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.NoDrag)
        self._multiple_selection_mode = boolean

    def connection_preview(self):

        self._connection_preview_item = EmptyItem(self._last_item_clicked.center())

        self.scene.addItem(self._connection_preview_item)
        self._connection_preview_item.setSelected(True)
        self._connection_preview_item.grabMouse()
        self._connection_preview = ConnectionView(self._last_item_clicked, self._connection_preview_item, self.scene)
        self._connection_preview.valid = False
        self.scene.addItem(self._connection_preview)

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            # To avoid the selection of multiple blocks outside multiple_selection_mode
            if len(self.selected_blocks()) < 2 and not self._multiple_selection_mode:
                [block.setSelected(False) for block in self.selected_blocks()]

            item = self.item_under_mouse()

            if isinstance(item, NodeView):
                if item.type == 'out':
                    self._last_item_clicked = item
                    self.connection_creation_mode = True
                    self.connection_preview()

        elif event.button() == Qt.RightButton:
            for item in self.items_under_mouse():
                if isinstance(item, ConnectionView):
                    pass
                elif isinstance(item, BlockView):
                    pass

        return super(PrairieView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):

        item = self.item_under_mouse()

        if self._connection_creation_mode:
            if isinstance(item, NodeView) and item != self._last_item_clicked:
                self.controller.connect_nodes(self._last_item_clicked, item)
            self.scene.removeItem(self._connection_preview)
            self.scene.removeItem(self._connection_preview_item)
            self.scene.update()
        self.connection_creation_mode = False
        return super(PrairieView, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        item = self.item_under_mouse()
        if isinstance(item, NodeView):
            item.highlight(True)

        if self._connection_creation_mode:
            if isinstance(item, NodeView):
                self._connection_preview.valid = True
            else:
                self._connection_preview.valid = False

        return super(PrairieView, self).mouseMoveEvent(event)

    def item_under_mouse(self):
        for item in self.items():
            if item.isUnderMouse():
                return item

    def items_under_mouse(self):
        for item in self.items():
            if item.isUnderMouse():
                yield item


    def node_under_mouse(self):
        for item in self.items():
            if item.isUnderMouse() and isinstance(item, NodeView):
                return item
        return -1

    def block_under_mouse(self):
        for item in self.items():
            if item.isUnderMouse() and isinstance(item, BlockView):
                return item
        return -1

    def blocks_under_mouse(self):
        return [block for block in self.items if BlockView.isUnderMouse() and isinstance(block, BlockView)]

    def function_block_under_mouse(self):
        for item in self.items():
            if item.isUnderMouse() and type(item) == FunctionBlockView:
                return item
        return -1

    def freeze_all_blocks(self, boolean):
        for item in self.items():
                if type(item) != ConnectionView:
                    item.setFlag(QGraphicsItem.ItemIsMovable, not boolean)

    def is_item_focus(self):
        for item in self.items():
            if item.hasFocus():
                return True
        return False

    def get_focus_item(self):
        for item in self.items():
            if item.hasFocus():
                return item

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.multiple_selection_mode = True
        elif self.multiple_selection_mode and event.key() == Qt.Key_S:
            dlg = QFileDialog()
            self.controller.save_file(str(dlg.getSaveFileName()[0].strip('.yml') + '.yml'))
        elif self.multiple_selection_mode and event.key() == Qt.Key_I:
            dlg = QFileDialog()
            if dlg.exec_():
                filename = dlg.selectedFiles()
            try:
                self.controller.load_file(str(filename[0]))
            except:
                print(filename)

        elif self.multiple_selection_mode and event.key() == Qt.Key_R:
            self.controller.reset_inputs()
            self.controller.run()

        elif self.multiple_selection_mode and event.key() == Qt.Key_D:
            print('Debug')

        # elif event.key() == Qt.Key_S:
        #     self.setDragMode(QGraphicsView.RubberBandDrag)
        #
        # elif event.key() == Qt.Key_E:
        #     self.setDragMode(QGraphicsView.ScrollHandDrag)

        super(PrairieView, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.multiple_selection_mode = False
        super(PrairieView, self).keyReleaseEvent(event)

    def wheelEvent(self, event):
        if os == 'Darwin':
            new_x = self.horizontalScrollBar().value() - event.pixelDelta().x()
            new_y = self.verticalScrollBar().value() - event.pixelDelta().y()
            self.horizontalScrollBar().setValue(new_x)
            self.verticalScrollBar().setValue(new_y)

        else:
            if self._multiple_selection_mode:
                # print(event.angleDelta().x())
                if event.angleDelta().y() > 0:
                    self.scale(config_doc['wheel_zoom'], config_doc['wheel_zoom'])
                    self.update()
                if event.angleDelta().y() < 0:
                    self.scale(1/config_doc['wheel_zoom'], 1/config_doc['wheel_zoom'])
                    self.update()

    def selected_items(self):
        return [item for item in self.items() if item.isSelected()]

    def selected_blocks(self):
        return [item for item in self.items() if isinstance(item, BlockView) and item.isSelected()]

    def set_edit_mode(self, boolean):
        if boolean:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def block_views(self):
        return {block.id: block for block in self.items() if isinstance(block, BlockView)}

    def dragEnterEvent(self, event):
        event.setAccepted(True)

        mime_data = event.mimeData().text()
        position = [event.pos().x(), event.pos().y()]

        _block = self.controller.create_block_from_dict(json.loads(mime_data))
        self._block_preview = self.controller.create_block_view_from_block(_block, position=position, preview=True)

        self.scene.addItem(self._block_preview)
        self._block_preview.setSelected(True)
        self._block_preview.grabMouse()

    def dragMoveEvent(self, event):
        if self._block_preview is not None:
            event_position = self.mapToScene(event.pos())
            block_size = [self._block_preview.rect.width() / 2, self._block_preview.rect.height() / 2]
            drop_position = [event_position.x() - block_size[1], event_position.y() - block_size[1]]

            self._block_preview.setPos(QPoint(*drop_position))

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        if self._block_preview is not None:
            self._block_preview.ungrabMouse()
            self.scene.removeItem(self._block_preview)
            self._block_preview = None

    def dropEvent(self, event):

        if self._block_preview is not None:
            self._block_preview.ungrabMouse()
            self.scene.removeItem(self._block_preview)

            event_position = self.mapToScene(event.pos())
            block_size = [self._block_preview.rect.width()/2, self._block_preview.rect.height()/2]

            drop_position = [event_position.x() - block_size[1], event_position.y() - block_size[1]]

            mime_data = event.mimeData().text()

            self.controller.add_block(self.controller.create_block_from_dict(json.loads(mime_data)),
                                      position=drop_position)

            self._block_preview = None

    def update_node_value(self, block_id, node_id, value):
        self.controller.update_node_value(block_id, node_id, value)

    def event(self, event: QEvent):

        # Mac zoom gesture
        if isinstance(event, QNativeGestureEvent):
            if event.gestureType() == Qt.ZoomNativeGesture:
                anchor = self.transformationAnchor()
                self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
                self.scale(1 + event.value(), 1 + event.value())
                self.setTransformationAnchor(anchor)

        return super(PrairieView, self).event(event)

    def get_connected_node_name(self, block_id, node_id):
        return self.controller.get_connected_node_name(block_id, node_id)

    def remove_connection(self, connection_view):
        self.controller.remove_connection(connection_view)