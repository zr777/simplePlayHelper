import subprocess
import sys
from PyQt4 import QtGui
import requests
import time

class PlayHelper(QtGui.QWidget):

    def __init__(self):
        super().__init__()
        self.tray = QtGui.QSystemTrayIcon(QtGui.QIcon('icon.png'), self)
        # http://www.iconfont.cn/search/index?searchType=icon&q=vedio
        self.tray.show()

    def play(self, url):
        print('hello here')
        self.tray.showMessage('Now Playing ...', url)
        # subprocess.call(['you-get', '-p', 'mpv', url])# Popen
        # https://stackoverflow.com/questions/89228/calling-an-external-command-in-python/89243#89243
        # cmd = ['you-get', '-p', 'mpv', url]
        cmd = ['mpv', url]
        
        p = subprocess.run(cmd,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        # time.sleep(1)
        # print(p.stdout.readline())
        # print(p.stdout.readlines())
        # retval = p.wait()

    def onClipChanged(self):
        if(QtGui.QApplication.clipboard().mimeData().hasText()):
            url = QtGui.QApplication.clipboard().text()
            try:
                if url.startswith('http'):
                # requests.get(text)
                # if QtGui.QSystemTrayIcon.supportsMessages():
                #    self.tray.showMessage('Now Playing ...', title)
                    self.play(url)
                else:
                    print('please copy a url')
            except Exception as e:
                print(e)

def main():

    app = QtGui.QApplication(sys.argv)

    w = PlayHelper()
    w.resize(250, 150)
    w.move(300, 300)
    w.setWindowTitle('playHelper')
    w.show()

    app.clipboard().dataChanged.connect(w.onClipChanged)
    sys.exit(app.exec_())

main()