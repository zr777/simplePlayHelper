import sys
from PyQt4 import QtGui

class Example(QtGui.QWidget):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.initUI()
        
    def initUI(self):
        
        okButton = QtGui.QPushButton("OK")
        cancelButton = QtGui.QPushButton("Cancel")

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(okButton)
        hbox.addWidget(cancelButton)

        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)
        
        #----
        chmenu = QtGui.QMenu()
        chmenu.addAction('testing')
        chmenu.addAction('testing1')
        
        a = QtGui.QAction("kill", self, triggered=self.kill)
        chmenu.addAction(a)
        self.action = a
        chmenu.addSeparator()
        
        a2 = QtGui.QAction("change", self, triggered=self.changeA)
        chmenu.addAction(a2)
        chmenu.addAction('testing2')
        okButton.setMenu(chmenu)
        
        self.btn = okButton
        #----
        
        
        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('Buttons')    
        self.show()
     
    def kill(self):
        print(dir(self.btn))
        help(self.btn)
        self.btn.menu().deleteLater()
        print('kill')

    def done(self):
        print('done')
        
    def changeA(self):
        # help(self.action.triggered)
        self.action.triggered.disconnect(self.kill)
        self.action.triggered.connect(self.done)

def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()