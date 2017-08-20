from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

class Window(QtGui.QWidget):
    '''
    from: https://stackoverflow.com/questions/32458111/pyqt-allign-checkbox-and-put-it-in-every-row
    other:
    https://pythonspot.com/en/qt4-table/
    http://www.cnblogs.com/findumars/p/5553367.html
    '''
    def __init__(self, rows, columns):
        QtGui.QWidget.__init__(self)
        self.table = QtGui.QTableWidget(rows, columns, self)
        # self.table.verticalHeader().setVisible(False)
        # 表头隐藏与否
        self.table.horizontalHeader().setVisible(False)
        # 增加多行选中效果
        self.table.setSelectionMode(QtGui.QAbstractItemView.MultiSelection);
        for row in range(rows):
            qwidget = QtGui.QWidget()
            checkbox = QtGui.QCheckBox()
            checkbox.setCheckState(QtCore.Qt.Unchecked)
            qhboxlayout = QtGui.QHBoxLayout(qwidget)
            qhboxlayout.addWidget(checkbox)
            qhboxlayout.setAlignment(Qt.AlignCenter)
            qhboxlayout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, qwidget)
            # self.table.setItem(row, 1, QtGui.QTableWidgetItem(str(row)))
            self.table.setCellWidget(row, 1, QtGui.QPushButton(str(row)))
        layout = QtGui.QVBoxLayout(self)
        self.button = QtGui.QPushButton()
        self.button.setObjectName("loadButton")
        layout.addWidget(self.table)
        layout.addWidget(self.button)
        self.button.clicked.connect(self.ButtonClicked)

    def ButtonClicked(self):
        '''
        http://pyqt.sourceforge.net/Docs/PyQt4/qabstractitemview.html#selectedIndexes
        '''
        selected = self.table.selectedIndexes() # return [QModelIndex]
        # print(selected)
        # print(dir(selected[0]))
        # print(selected[0].row())
        checked_list = []
        for i in selected[::2]:
            print(self.table.cellWidget(i.row(), 1).text()) # return Qwidget object


if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window(3, 2)
    window.resize(350, 300)
    window.show()
    sys.exit(app.exec_())