# 思路：https://www.v2ex.com/t/246998
# QT重要参考: http://zetcode.com/gui/pyqt4/
# QT多线程：https://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
import sys
from PyQt4 import (QtGui, QtCore)
import subprocess
from functools import partial
from collections import OrderedDict
import requests
import time

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
ua = UserAgent()
headers = {'user-agent': ua.chrome}


class PlayHelper(QtGui.QDialog):

    def __init__(self):
        '''
        You can find icon from http://www.iconfont.cn/search/index?searchType=icon&q=vedio
        
        '''
        self.app = QtGui.QApplication(sys.argv)
        super().__init__()
        self.icons = self.createIcons()
        self.status = {'pauseIsChecked': False}
        self.createTray(icon_text='播放助手')
        self.createMainLayout()
        self.log = Log()
        self.handleHistroy()
        
        self.downloader = Downloader()
        
    def run(self, title='playHelper'):
        # w.move(300, 300)
        self.resize(600, 450)
        self.setWindowTitle(title)
        self.show()
        self.app.clipboard().dataChanged.connect(self.onClipChanged)
        sys.exit(self.app.exec_())
        
    def createIcons(self):
        return {
            'smile': QtGui.QIcon('smile.png'),
            'vedio': QtGui.QIcon('icon.png'),
            'history': QtGui.QIcon('list_icon.png'),
        }
        
    def createMenuActions(self):
        return [
            # QtGui.QAction("log", self, triggered=),
            QtGui.QAction("更新下载器", self, triggered=self.upgrade),
            QtGui.QAction("刷新", self, triggered=self.refresh),
            QtGui.QAction("恢复窗口", self, triggered=self.restoreWindow),
            '---',
            QtGui.QAction("暂停", self,
                          # shortcut='Ctrl+E',
                          statusTip='是否监控剪贴板',
                          triggered=self.pause,
                          checkable=True,),
            QtGui.QAction("退出", self,
                          statusTip="退出应用",
                          triggered=self.shutdown,),
        ]
        
    def shutdown(self):
        # ...
        self.saveHistory()
        QtGui.qApp.quit()

    def closeEvent(self, event):
        '''
        覆写关闭窗口函数
        '''
        if self.tray.isVisible():
            # QtGui.QMessageBox.information(self, "playHelper",
                                          # '播放助手将隐藏<br>'
                                          # '<b>退出</b>请右击系统托盘')
            self.hide()
            event.ignore() # 阻断关闭信号的传输
            
    def pause(self, isChecked):
        '''
        调试时在传参中添加*args, **kwargs, 并print(args, kwargs)
        即可看到传入事件对象的内容
        系统托盘菜单中暂停栏勾选状态改变
        '''
        self.status['pauseIsChecked'] = isChecked
        
    def createTray(self, icon_text):
        '''
        创建系统托盘图标显示控件
        '''
        self.createTrayMenu()
        self.createTrayIcon(icon_text)


    def createTrayMenu(self):
        '''
        系统托盘右键菜单
        '''
        m = QtGui.QMenu()
        h = QtGui.QMenu("历史记录")
        m.addMenu(h)
        
        for i in self.createMenuActions():
            if i == '---':
                m.addSeparator()
            else:
                m.addAction(i)

        self.menu, self.historyMenu = m, h
        
    def createTrayIcon(self, icon_text):
        '''
        系统托盘图标设置
        '''
        i = self.icons['vedio']
        t = QtGui.QSystemTrayIcon()
        t.setIcon(i)
        t.setContextMenu(self.menu)
        t.show()
        t.setToolTip(icon_text)
        # 设置图标点击事件处理
        t.activated.connect(self._trayIconActivated)
        
        self.icon, self.tray = i, t
    
    def _trayIconActivated(self, reason):
        if reason == self.tray.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
        
    def showInfo(self, title, info):
        self.tray.showMessage(title, info)   
        
    def refresh(self):
        self.lives.start()
        
    def createMainLayout(self):
        '''
        http://www.cnblogs.com/jakeyChen/articles/4097683.html
        http://blog.csdn.net/fengyu09/article/details/39639413
        '''
        mainLayout = QtGui.QVBoxLayout()
        self.setLayout(mainLayout)

        toolbox = QtGui.QToolBox()
        mainLayout.addWidget(toolbox)
        
        self.lives = Lives()
        self.lives.dataReady.connect(
            partial(self.createItemForToolbox, toolbox))
        self.refresh()  # self.lives.start()
    
    def createItemForToolbox(self, toolbox, item_dict):
        # print(dir(toolbox))
        for i in range(toolbox.count()):
            toolbox.removeItem(0) # toolbox.removeItem(i) !! wrong
        for name, list_ in item_dict.items():
            groupbox = QtGui.QGroupBox()
            inner_layout = QtGui.QVBoxLayout(groupbox)
            # inner_layout.setMargin(10)
            # inner_layout.setAlignment(QtCore.Qt.AlignCenter)
            for text, url, icon in list_:
                if icon == None:
                    icon = self.icons['smile']
                el = self.createMainButton(text, icon)
                el.clicked.connect(partial(self.play, url, text))
                inner_layout.addWidget(el)
            # inner_layout.addStretch()
            toolbox.addItem(groupbox, name)
        # toolbox.adjustSize()
        # self.adjustSize()
            
    def createMainButton(self, text, icon):
        # b = QtGui.QToolButton()
        b = QtGui.QPushButton()
        b.setText(text)
        b.setIcon(icon)
        b.setIconSize(QtCore.QSize(30, 30))
        # b.setAutoRaise(True)
        # b.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        return b

    def play(self, url, title=None):
        '''
        调用mpv 或者联合 you-get 播放链接视频
        https://stackoverflow.com/questions/89228/calling-an-external-command-in-python/89243#89243
        
        '''
        # print('hello here')
        self.log(title, title='视频名称', hide=True)
        self.tray.showMessage('即将播放...', title if title else url)
        self.addToHistory(url, title)
        # subprocess.call(['you-get', '-p', 'mpv', url])# Popen # run
        # 
        if 'douyu' in url or 'zhanqi' in url or 'panda' in url:
            cmd = ['you-get', '-p', 'mpv', url]
        else:
            cmd = ['mpv', url]
        
        p = subprocess.Popen(cmd, shell=True,)
                           # stdout=subprocess.PIPE,
                           # stderr=subprocess.STDOUT)
        # time.sleep(1)
        # print(p.stdout.readline())
        # 
        # p = subprocess.run(cmd, shell=True, timeout=5, stdout=subprocess.PIPE)
        # print(p.stdout.readlines())
        # retval = p.wait()

    def getInfoFromYouget(self, url):
        import chardet
        info = subprocess.check_output(['you-get', '-i', url], timeout=2)
        for i in info.splitlines():
            try:
                i = i.decode(chardet.detect(i)['encoding'])
                if i.lower().startswith('title'):
                    return i[6:].strip()
            except:
                print('解码错误')
        return '获取信息失败'

    def onClipChanged(self):
        if(not self.status['pauseIsChecked'] and 
           QtGui.QApplication.clipboard().mimeData().hasText()
        ):
            url = QtGui.QApplication.clipboard().text()
            try:
                #import re
                if url.startswith('http://') or url.startswith('https://'):
                # requests.get(text)
                # if QtGui.QSystemTrayIcon.supportsMessages():
                #    self.tray.showMessage('Now Playing ...', title)
                    # print(help(self.historyMenu.addAction))
                    title = self.getInfoFromYouget(url)
                    self.play(url, title)
                else:
                    print('please copy a url')
            except Exception as e:
                print(e)
    
    def handleHistroy(self):
        self.f_history = './_history'
        self.loadHistroy()
        self.temp_history = []
    
    def addToHistory(self, url, title=None, addtotemp=True):
        actions = self.historyMenu.actions()
        # debug: print([i.text() for i in actions])
        if len(actions) >= 20:
            first_a = actions[0]
            self.historyMenu.removeAction(first_a)
            del first_a
            
        if addtotemp:
            self.temp_history.append([time.ctime(), title, url])
            # print(self.temp_history)
        
        self.historyMenu.addAction(
            QtGui.QAction(
                self.icons['history'],
                title if title else url,
                self,
                triggered=partial(self.play, url, title)
            ))

    def loadHistroy(self):
        try:
            with open(self.f_history, 'r', encoding='utf-8') as f:
                for i in f.readlines()[-20:]:
                    _, title, url = i.split(',')
                    self.addToHistory(url, title, addtotemp=False)
        except Exception as e:
            print(e, '没有发现历史文件')
        
    def saveHistory(self):
        # import os.path
        # if os.path.isfile(fname):
        # actions = self.historyMenu.actions()
        if self.temp_history:
            with open(self.f_history, 'a', encoding='utf-8') as f:
                f.write(
                    '\n'.join(
                        [','.join(i) for i in self.temp_history]))
                f.write('\n')
        
    def upgrade(self):
        # self.log('正在更新, 请稍候...', title='更新信息')
        print()
        temp_text = ''
        for cmd in (
            ['pip', 'install', '--upgrade', 'youtube-dl'],
            ['pip', 'install', '--upgrade', 'you-get'],
        ):
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            p.wait()
            temp_text += '返回码: <b>{}</b> <br/> 输出: {} <br/>'.format(
                p.returncode, p.stdout.readlines())
        self.log(temp_text, title='更新信息')

    def restoreWindow(self):
        self.showNormal()
        self.log.showNormal()


class Log(QtGui.QWidget):
    
    log_text = ''

    def __init__(self):
        super(Log, self).__init__()
        
        self.initUI()
    
    def initUI(self):

        title = QtGui.QLabel('标题')
        self.titleEdit = QtGui.QLineEdit()
        
        info = QtGui.QLabel('信息')
        self.infoEdit = QtGui.QTextEdit()

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(title, 1, 0)
        grid.addWidget(self.titleEdit, 1, 1)

        grid.addWidget(info, 2, 0)
        grid.addWidget(self.infoEdit, 2, 1, 5, 1)
        # last 2: row span and column span
        
        self.setLayout(grid) 

        self.resize(300, 200)
        self.setWindowTitle('log info')    
        self.hide()

    def __call__(self, text='i am log', title='log', hide=False):
        self.log_text += ''.join([
            '<b>', time.ctime(), '</b>'
            '<br/>---------------<br/>',
            text, '<br/>'])
        self.log_text = self.log_text[:10000]
        self.titleEdit.setText(title)
        self.infoEdit.setText(self.log_text)
        self.infoEdit.moveCursor(QtGui.QTextCursor.End)
        if not hide: 
            self.show()
        
    def closeEvent(self, event):
        '''
        覆写关闭窗口函数
        '''
        self.hide()
        event.ignore()


class Lives(QtCore.QThread):

    dataReady = QtCore.pyqtSignal(OrderedDict)
    
    def run(self):
        self.dataReady.emit(OrderedDict([
            ('bilibili', Lives.get_bilibili_recommend()),
            ('熊猫', Lives.get_panda_recommend()),
            ('斗鱼', Lives.get_douyu_recommend()),
            ('战旗', Lives.get_zhanqi_recommend()),
        ]))
        # while 1: import time
            # time.sleep(10)
    
    @staticmethod    
    def get_bilibili_recommend():
        url = 'https://www.bilibili.com/'
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, 'lxml')
        return [(i['title'], url + i['href'], None)
                for i in soup.select('.groom-module a')]
    
    @staticmethod    
    def get_zhanqi_recommend():
        url = 'https://www.zhanqi.tv'
        res = requests.get(url + '/lives', headers=headers)
        soup = BeautifulSoup(res.content, 'lxml')
        return [(i.select_one('.name').text, url + i['href'], None)
                for i in soup.select('.js-jump-link')]
    
    @staticmethod
    def get_panda_recommend():
        url = 'https://www.panda.tv'
        res = requests.get(url + '/all', headers=headers)
        soup = BeautifulSoup(res.content, 'lxml')
        return [(i.select_one('.video-title').text, url + i['href'], None)
                for i in soup.select('.video-list-item-wrap')]
    
    @staticmethod
    def get_douyu_recommend():
        url = 'https://www.douyu.com'
        res = requests.get(url + '/directory/all', headers=headers)
        soup = BeautifulSoup(res.content, 'lxml')
        return [(i['title'], url + i['href'], None)
                for i in soup.select('#live-list-contentbox .play-list-link')]

class Downloader(QtGui.QWidget):
    
    def __init__(self):
        super(Downloader, self).__init__()
        
        self.initUI()
        
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
        
    def timerEvent(self, e):
      
        if self.step >= 100:
        
            self.timer.stop()
            self.btn.setText('Finished')
            return
            
        self.step = self.step + 1
        self.pbar.setValue(self.step)

    def doAction(self):
      
        if self.timer.isActive():
            self.timer.stop()
            self.btn.setText('Start')
            
        else:
            self.timer.start(100, self)
            self.btn.setText('Stop')
                
                
def main():
    play_helper = PlayHelper()
    play_helper.run()

main()