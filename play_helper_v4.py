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
from threading import Thread
from queue import Queue, Empty
import io

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
        b = QtGui.QPushButton('下载')
        b.clicked.connect(self.download)
        mainLayout.addWidget(toolbox)
        mainLayout.addWidget(b)
        
        self.addSearchItemForToolbox(toolbox)
        
        self.lives = Lives()
        self.lives.dataReady.connect(
            partial(self.createItemsForToolbox, toolbox))
        self.refresh()  # self.lives.start()
    
    def addSearchItemForToolbox(self, toolbox):
        '''
        http://zetcode.com/gui/pyqt4/layoutmanagement/
        '''
        searchEdit = QtGui.QLineEdit('请填入搜索内容')
        goButton = QtGui.QPushButton("Go")
        goButton.clicked.connect(self.searchDisplay)
        
        hbox = QtGui.QHBoxLayout()
        # hbox.addStretch(1)
        hbox.addWidget(searchEdit)
        hbox.addWidget(goButton)
        
        qwidget = QtGui.QWidget()
        serach_layout = QtGui.QVBoxLayout(qwidget)
        serach_layout.addLayout(hbox)
        # table_layout.addWidget(table)
        toolbox.addItem(qwidget, '搜索')

        self.searchEdit = searchEdit
        self.serach_layout = serach_layout

    def searchDisplay(self):
        try:
            self.serach_layout.removeWidget(self.search_table)
        except:
            pass
        t = self.searchEdit.text()
        list_ = self._search(t) # list_ -> [(text, url, icon) ...]
        table = self.createItemForToolBox(list_)
        self.search_table = table
        self.serach_layout.addWidget(table)
    
    def _search(self, text):
        bi_S_url = 'https://search.bilibili.com/all?keyword={}'.format(text)
        res = requests.get(bi_S_url, headers=headers)
        soup = BeautifulSoup(res.content, 'lxml')
        return [(i['title'], 'https:' + i['href'].split('?')[0], None)
                for i in soup.select('.title')]

    def createItemsForToolbox(self, toolbox, item_dict):
        # print(dir(toolbox))
        '''
        先清空所有内容然后添加新内容
        '''
        for i in range(toolbox.count()):
            toolbox.removeItem(1) # toolbox.removeItem(i) !! wrong
            # toolbox.removeItem(0) # 不请空搜索栏
        
        self.tables = []
        for name, list_ in item_dict.items():
            table = self.createItemForToolBox(list_)
            self.tables.append(table)
            
            # 方法一：比二更有层次感
            qwidget = QtGui.QWidget()
            table_layout = QtGui.QVBoxLayout(qwidget)
            table_layout.addWidget(table)
            toolbox.addItem(qwidget, name)
            # 方法二：与法一基本相同
            # toolbox.addItem(table, name)
            
        # toolbox.adjustSize()
        # self.adjustSize()
    
    def download(self):
        d_list = []
        for t in self.tables:
            selected = t.selectedIndexes()
            for i in selected[::1]:
                b = t.cellWidget(i.row(), 0)
                # url = b.url
                # print(url)
                d_list.append([b.text(), b.url])
        self.downloader(d_list)
    
    def __old_createItemForToolBox(self, list_):
        groupbox = QtGui.QGroupBox()
        inner_layout = QtGui.QHBoxLayout(groupbox)
        # inner_layout.setMargin(10)
        # inner_layout.setAlignment(QtCore.Qt.AlignCenter)
        for text, url, icon in list_:
            if icon == None:
                icon = self.icons['smile']
            el = self.createMainButton(text, icon)
            el.clicked.connect(partial(self.play, url, text))
            inner_layout.addWidget(el)
        # inner_layout.addStretch()
        return groupbox

    def createItemForToolBox(self, list_):
        '''
        每个toolbox单元由一个表格构成。
        详细设置细节解释请参考:
        http://www.cnblogs.com/zhoug2020/p/3789076.html
        http://www.cnblogs.com/findumars/p/5553367.html
        http://www.myexception.cn/qt/178315.html
        '''
        rows, columns = len(list_), 1
        t = QtGui.QTableWidget(rows, columns)
        t.horizontalHeader().setVisible(False)
        t.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) # MultiSelection
        t.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        for row, (text, url, icon) in enumerate(list_):
            if icon == None:
                icon = self.icons['smile']
            el = self.createMainButton(text, icon)
            el.url = url
            el.clicked.connect(partial(self.play, url, text))
            t.setCellWidget(row, 0, el)
        # inner_layout.addStretch()
        
        # t.resizeColumnsToContents()
        t.resizeRowsToContents()
        # 水平表头设置
        # t.horizontalHeader().resizeSection(0, self.width()) # 设置指定表宽度
        t.horizontalHeader().setStretchLastSection(True) # 设置充满表宽度
        # 垂直表头设置
        # t.verticalHeader().setMovable(False)
        t.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        # 设置垂直表头大小不可修改
        t.verticalHeader().setFixedWidth(32)  # 设置表头宽度
        t.verticalHeader().setDefaultAlignment(QtCore.Qt.AlignCenter)
        t.setShowGrid(False)  # 设置不显示格子线
        return t

    def createMainButton(self, text, icon):
        # b = QtGui.QToolButton()
        b = QtGui.QPushButton()
        b.setText(text)
        b.setIcon(icon)
        b.setIconSize(QtCore.QSize(30, 30))
        b.setStyleSheet("QPushButton {text-align : left;}")
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
                    try:
                        if i != '\n':
                            _, title, url = i.split(',mwr,')
                            self.addToHistory(url, title, addtotemp=False)
                    except Exception as e:
                        self.log(repr(e), title='读取历史文件出错')
        except Exception as e:
            self.log(repr(e), title='没有发现历史文件')
        
    def saveHistory(self):
        # import os.path
        # if os.path.isfile(fname):
        # actions = self.historyMenu.actions()
        if self.temp_history:
            with open(self.f_history, 'a', encoding='utf-8') as f:
                f.write(
                    '\n'.join(
                        [',mwr,'.join(i) for i in self.temp_history]))
                f.write('\n')
        
    def upgrade(self):
        from PyQt4 import QtTest
        self.log('正在更新, 不要动作, 请稍候...', title='更新信息')
        QtTest.QTest.qWait(200) # 给UI时间来展示

        # self.downloader.popMessage('更新中，请不要动作')
        temp_text = ''
        for cmd in (
            ['pip', 'install', '--upgrade', 'youtube-dl'],
            ['pip', 'install', '--upgrade', 'you-get'],
        ):
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            p.wait()
            temp_text += '返回码: <b>{}</b> <br/> 输出: {} <br/>'.format(
                p.returncode,
                '<br/>'.join([i.decode() for i in p.stdout.readlines()])
            )
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

        # self.resize(300, 200)
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
        url = 'https://www.bilibili.com'
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, 'lxml')
        return [(i['title'], url + i['href'], None)
                for i in soup.select('.groom-module a')]
    
    @staticmethod    
    def get_zhanqi_recommend():
        url = 'https://www.zhanqi.tv'
        res = requests.get(url + '/lives', headers=headers)
        soup = BeautifulSoup(res.content, 'lxml')
        info = [(i.select_one('.name').text, url + i['href'], None)
                for i in soup.select('.js-jump-link')]

        url2 = 'https://www.zhanqi.tv/api/static/v2.1/game/live/6/30/1.json'
        rooms = requests.get(url2, headers=headers).json()['data']['rooms']
        info2 = [(i['title'], url + i['url'], None)
                 for i in rooms]
        return info + info2
    
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

# namedtuple is immutable ！！！不能使用
# 异常处理不要轻易pass，否则debug时很可能忽略
# from collections import namedtuple                
# Task_d = namedtuple('Task_d', ['pbar', 'btn', 'process', 'step'])
class Task_d():
    __slots__ = ('pbar', 'btn', 'process', 'step')

    def __init__(self, pbar, btn, process, step=0):
        self.pbar = pbar
        self.btn = btn
        self.process = process
        self.step = step
        
class Downloader(QtGui.QWidget):
    
    io_q = Queue()
    
    def __init__(self):
        super(Downloader, self).__init__()
        self.initUI()
        self.timer = QtCore.QBasicTimer()
        self.tasks = {}
        self.tasksNum = 0
        self.position = 0
        
    def initUI(self): 

        self.grid = QtGui.QGridLayout()  # grid.setSpacing(10) 
        self.setLayout(self.grid)
        self.setGeometry(300, 300, 280, 100)
        self.setWindowTitle('下载列表')
        # self.show()
        self.hide()

    def __call__(self, list_):
        self.show()
        if not self.timer.isActive():
            self.clearOldTaskUI()
            res = []
            for name, url in list_:
                res.append(self.createTask(name, url))
            if all(res):  # 如果所有任务都是已经完成的
                self.hide()
                self.popMessage()
            else:
                self.timer.start(500, self)    
                Thread(target=self.calculate_steps).start()
        else:
            for name, url in list_:
                self.createTask(name, url)
    
    def popMessage(self, text='所选任务已经下载过'):
        '''
        http://www.programcreek.com/python/example/62361/PyQt4.QtGui.QMessageBox
        '''
        self.m = m = QtGui.QMessageBox() # 必须要有一个引用
        m.setWindowTitle('信息')
        # m.setWindowIcon()
        m.setText(text)
        m.setIcon(QtGui.QMessageBox.Warning)
        m.show()
    
    def clearOldTaskUI(self):
        self.position = 0
        # delete = self.grid.removeItem
        item = self.grid.itemAt
        for i in range(self.grid.count()):
            item(i).widget().deleteLater()  # 删除对象
        # for i in self.tasks.values():
            # delete(i.pbar)
            # delete(i.btn)
                
    def createTask(self, name, url):
        if not self.tasks.get(name, None):
            pbar, btn = self.createTaskUI(name)
            process = self._download(name, url)
            self.tasks[name] = Task_d(pbar, btn, process)
            self.tasksNum += 1
            return False
        else:
            return True  # 表明已经下载过了

    def createTaskUI(self, name):
        p = self.position
        
        title = QtGui.QLabel(name)
        self.grid.addWidget(title, p, 0, 1, 2)
        
        pbar = QtGui.QProgressBar()
        # pbar.setGeometry(30, 40, 200, 25)
        self.grid.addWidget(pbar, p + 1, 0)
        
        btn = QtGui.QPushButton('等待中...')
        btn.setText('下载中...')
        # self.btn.clicked.connect(self.doAction)
        self.grid.addWidget(btn, p + 1, 1)
        
        self.position = p + 2  # 3亦可
        return pbar, btn
    
    def _download(self, name, url):
        '''
        youtube-dl 得到的下载信息基本都是\r结尾的，所以采用这种方式。
        '''
        p = subprocess.Popen(['youtube-dl', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        reader = io.TextIOWrapper(p.stdout, newline='\r')  # !!!!
        # io.BytesIO(p.stdout) # io.TextIOBase
        Thread(target=partial(self.stream_watcher, name, reader)).start()
        return p
        
    def stream_watcher(self, name, reader):
        '''
        subprocess.Popen.communicate 会全部累积到缓冲区，不行
        '''
        for line in reader:
            if line:
                self.io_q.put((name, line))

        if not reader.closed:
            reader.close()

        self.tasksNum -= 1
            
    def calculate_steps(self):
        while True:
            try:
                name, line = self.io_q.get(block=True, timeout=0.2)# get_nowait()
            except Empty:
                # if task.poll() is not None:
                if self.tasksNum == 0:
                    # 不能在另一线程中调用主线程的timer
                    # self.timer.stop()
                    return  # break
            else:
                words = line.strip().split()
                if len(words) > 2 and words[0] == '[download]':
                    try:
                        step = int(float(words[1][:-1]))
                        self.tasks[name].step = step
                        # print('((', name, '))', step)     
                    except Exception as e:
                        raise e

    def timerEvent(self, e):
        '''
        不要使用阻塞代码，会使UI失去响应
        '''
        for t in self.tasks.values():
            try:
                t.pbar.setValue(t.step)

                if t.step == 100:
                    t.btn.setText('完成！')
            except:
                pass # the ui is deleted 
                # 或者在删除旧ui界面中去除self.tasks中的旧任务

        # print('任务数：', self.tasksNum)
        if self.tasksNum == 0:
            self.timer.stop()
        # timer 不停止?

    def closeEvent(self, event):
        '''
        覆写关闭窗口函数
        '''
        self.hide()
        event.ignore()


def main():
    play_helper = PlayHelper()
    play_helper.run()

main()