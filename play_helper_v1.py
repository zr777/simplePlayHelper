# 思路：https://www.v2ex.com/t/246998
# QT重要参考: http://zetcode.com/gui/pyqt4/
# QT多线程：https://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
import sys
from PyQt4 import (QtGui, QtCore)
import subprocess
from functools import partial
import requests

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
        
    def run(self, title='playHelper'):
        # w.move(300, 300)
        # self.resize(400, 300)
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
            QtGui.QAction("恢复窗口", self, triggered=self.showNormal),
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
        
    def createMainLayout(self):
        '''
        http://www.cnblogs.com/jakeyChen/articles/4097683.html
        http://blog.csdn.net/fengyu09/article/details/39639413
        '''
        mainLayout = QtGui.QVBoxLayout()
        self.setLayout(mainLayout)

        toolbox = QtGui.QToolBox()
        mainLayout.addWidget(toolbox)

        for name, list_ in {
            '战旗': PlayHelper.get_zhanqi_recommend(),
            'bilibili': PlayHelper.get_bilibili_recommend(),
            '熊猫': PlayHelper.get_panda_recommend(),
            '斗鱼': PlayHelper.get_douyu_recommend(),
        }.items():
            groupbox = QtGui.QGroupBox()
            inner_layout = QtGui.QVBoxLayout(groupbox)    
            # inner_layout.setMargin(10)
            # inner_layout.setAlignment(QtCore.Qt.AlignCenter)
            for text, url, icon in list_:
                if icon == None:
                    icon = self.icons['smile']
                el = self.createMainButton(text, icon)
                el.clicked.connect(partial(self.play, url))
                inner_layout.addWidget(el)
            # inner_layout.addStretch()
            toolbox.addItem(groupbox, name)

    def createMainButton(self, text, icon):
        # b = QtGui.QToolButton()
        b = QtGui.QPushButton()
        b.setText(text)
        b.setIcon(icon)
        b.setIconSize(QtCore.QSize(80, 80))
        # b.setAutoRaise(True)
        # b.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        return b

    def play(self, url):
        '''
        调用mpv 或者联合 you-get 播放链接视频
        https://stackoverflow.com/questions/89228/calling-an-external-command-in-python/89243#89243
        
        '''
        print('hello here')
        self.tray.showMessage('即将播放...', url)
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

    def onClipChanged(self):
        if(not self.status['pauseIsChecked'] and 
           QtGui.QApplication.clipboard().mimeData().hasText()
        ):
            url = QtGui.QApplication.clipboard().text()
            try:
                if url.startswith('http'):
                # requests.get(text)
                # if QtGui.QSystemTrayIcon.supportsMessages():
                #    self.tray.showMessage('Now Playing ...', title)
                    # print(help(self.historyMenu.addAction))
                    self.historyMenu.addAction(
                        QtGui.QAction(
                            self.icons['history'],
                            url, self,
                            triggered=partial(self.play, url)
                    ))
                    self.play(url)
                    
                else:
                    print('please copy a url')
            except Exception as e:
                print(e)

    def upgrade(self):
        cmd1 = 'pip install --upgrade youtube-dl'

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



                
def main():
    play_helper = PlayHelper()
    play_helper.run()

main()