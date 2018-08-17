from PyQt5.QtChart import QChart, QChartView, QCategoryAxis
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class ChartView(QChartView):
    def __init__(self, chart, parent=None):
        super(ChartView, self).__init__(chart, parent=parent)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Plus:
            self.chart().zoomIn()
        elif event.key() == Qt.Key_Minus:
            self.chart().zoomOut()


class Chart(QChart):
    def __init__(self, parent=None):
        super(Chart, self).__init__(parent=parent)
        title_font = QFont('Roboto', pointSize=8)
        labels_font = QFont('Roboto', pointSize=2)
        self.setTitleFont(title_font)
        self.axesX = QCategoryAxis()
        self.axesY = QCategoryAxis()
        self.axesX.setLabelsFont(labels_font)
        self.axesY.setLabelsFont(labels_font)
        self.setAxisX(self.axesX)
        self.setAxisY(self.axesY)

    def gestureEvent(self, event):
        if event.gesture(Qt.PanGesture):
            pass

    def sceneEvent(self, event):
        if event.type() == QEvent.GraphicsSceneWheel:
            if event.delta() > 0:
                self.zoom(1.05)
            if event.delta() < 0:
                self.zoom(0.95)
        return super(Chart, self).sceneEvent(event)

    def wheelEvent(self, event):
        return super(Chart, self).wheelEvent(event)
