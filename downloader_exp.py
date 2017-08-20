import sys
from PyQt4 import QtGui, QtCore
from subprocess import Popen, PIPE
from threading import Thread
from queue import Queue, Empty
import io

class Downloader(QtGui.QWidget):
    
    io_q = Queue()
    
    def __init__(self, url='https://www.bilibili.com/video/av13413193/'):
        super(Downloader, self).__init__()
        self.initUI()
        self.url = url
        
    def initUI(self):      

        self.pbar = QtGui.QProgressBar(self)
        self.pbar.setGeometry(30, 40, 200, 25)

        self.btn = QtGui.QPushButton('Start', self)
        self.btn.move(40, 80)
        self.btn.clicked.connect(self.doAction)

        self.timer = QtCore.QBasicTimer()
        self.step = 0
        
        self.setGeometry(300, 300, 280, 170)
        self.setWindowTitle('QtGui.QProgressBar')
        self.show()
        
    def download(self, url):
        '''
        http://sharats.me/the-ever-useful-and-neat-subprocess-module.html
        https://stackoverflow.com/questions/34447623/wrap-an-open-stream-with-io-textiowrapper
        https://stackoverflow.com/questions/8980050/persistent-python-subprocess
        https://docs.python.org/3/library/io.html#io.TextIOBase
        youtube-dl 得到的下载信息基本都是\r结尾的，所以采用这种方式。
        '''
        self.over = False
        self.proc = p = Popen(['youtube-dl', url], stdout=PIPE, stderr=PIPE)
        self.reader = io.TextIOWrapper(p.stdout, newline='\r')  # !!!!
        # io.BytesIO(p.stdout) # io.TextIOBase
        self.thread = Thread(target=self.stream_watcher, name='stdout-watcher').start()
        
        
    def stream_watcher(self):
        '''
        subprocess.Popen.communicate 会全部累积到缓冲区，不行
        https://docs.python.org/3.6/library/subprocess.html#subprocess.Popen.stdout
        https://stackoverflow.com/questions/18727282/read-subprocess-output-multi-byte-characters-one-by-one
        https://stackoverflow.com/questions/41792101/flask-break-line-subprocess-stdout-python3
        '''
        # while 1:
            # if self.over:
                # print('88 from night watcher')
                # break
            # try:
                # outs = self.reader.readline()
            # except IOError:
                # print('ioerror')
            # else:
                # for line in outs.splitlines():
                    # if line:
                        # self.io_q.put(line)

        for line in self.reader:
            # print(line)
            # print('^^^^^^^^^^^^^^^^^^^^^^^^^')
            if line:
                self.io_q.put(line)
   
        if not self.reader.closed:
            self.reader.close()
        
    def timerEvent(self, e):
        '''
        不要使用阻塞代码，会使UI失去响应
        '''
        try:
            line = self.io_q.get_nowait()
            # print(line)
        except Empty:
            # print('------****------')
            if self.proc.poll() is not None:
                # Popen.poll()检查子进程是否已结束，设置并返回returncode属性。
                # https://docs.python.org/3.6/library/subprocess.html#subprocess.Popen.poll
                print('*** i am over ***')
                self.over = True
                return
        else:
            words = line.strip().split()
            # print(words)
            if len(words) > 2 and words[0] == '[download]': # b'[download]'
                try:
                    step = int(float(words[1][:-1]))
                    # print(step)
                    # self.step = self.step
                    self.pbar.setValue(step)
                    if step == 100:
                        self.timer.stop()
                        self.btn.setText('Finished')
                        self.over = True
                except:
                    pass

    def doAction(self):
        if not self.timer.isActive():
            self.download(self.url)
            self.timer.start(500, self)
            self.btn.setText('...')
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Downloader()# sys.argv[1]
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()    