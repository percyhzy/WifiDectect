import queue #提供了同步队列类，可以在多线程编程中使用。
import random #生成随机数
import subprocess #生成子进程，以便在Python中运行外部命令。
import threading 
import time

import re #正则表达式
import chardet #检测字符编码
from PyQt6.QtCharts import QLineSeries #绘图功能，QLineSeries 用于绘制线图
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QPointF, QTimer #提供了核心功能，线程 (QThread)、信号 (pyqtSignal)、互斥锁 (QMutex)、定时器 (QTimer) 和点 (QPointF)。
from PyQt6.QtWidgets import QMainWindow, QMessageBox #提供了窗口部件，MainWindow 和 QMessageBox。
from ptyprocess import PtyProcessUnicode, PtyProcess #伪终端的进程处理

from .ui.appgui import Ui_MainWindow #
from .utils import get_wifi_signal_level, get_around_ssid_signal_level

mutex = QMutex() #全局变量，PyQt的互斥锁 (QMutex)，用于保护共享数据的访问。
ssid_mutex = QMutex() 
ssid_dict_lock = threading.Lock()#Python的标准线程锁 (threading.Lock)，用于保护字典的访问。
level_data = []   # 存储WiFi信号强度数据的列表
around_ssid_level_dict = {} #存储周围SSID信号强度数据的字典


def output_reader(proc, outq): #读取子进程的输出，子进程对象和输出队列，用于存储读取的输出数据，防止阻塞主线称
    for line in iter(proc.stdout.readline, b''): #创建一个迭代器，用于逐行读取子进程的标准输出，读到行尾空字符串。
        outq.put(line.decode('utf-8')) #对于每一行，使用 line.decode('utf-8') 将其从字节编码转换为字符串。将转换后的字符串放入输出队列 outq 中


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None): #类 MainWindow 的构造函数。它初始化 GUI 元素并连接按钮按下事件到相应的处理函数，没父对
        super().__init__(parent)#构造函数
        self.setupUi(self)#调用 setupUi 方法，初始化图形用户界面（GUI）组件，Ui_MainWindow中
        self.btn_infobutton.pressed.connect(self.info_button_press)#将 GUI 中的各个按钮的按下事件连接到相应的处理函数。例如，当 btn_infobutton 按钮被按下时，将调用 info_button_press 方法。
        self.btn_scanbutton.pressed.connect(self.scan_button_press)
        self.btn_graphybutton.pressed.connect(self.graphy_button_press)
        self.about_button.pressed.connect(self.about_button_press)
        self.btn_ssid_button.pressed.connect(self.ssid_graphy_button_press)
        # self.refreshThread = RefreshThread()
        # self.refreshThread.text.connect(self.update_label)
        #self.refreshThread.start()
        self.timer = QTimer() #创建一个 QTimer 定时器实例，并将其 timeout 信号连接到 update_chart 和 update_ssid_chart 方法。定时器每隔 1000 毫秒（1秒）触发一次，以定期更新图表。
        self.timer.timeout.connect(self.update_chart)
        self.timer.timeout.connect(self.update_ssid_chart)
        self.timer.start(1000)
        self.scanThread = None #表示尚未创建扫描线程
        self.is_scanning = False #当前没有进行扫描

        self.dataUpdateThread = DataThread() #创建并启动一个 DataThread 线程，用于定期更新 WiFi 信号强度数据
        self.dataUpdateThread.start() 

        self.ssidLevelUpdateThread = SSID_DataThread()
        self.ssidLevelUpdateThread.start()

    def closeEvent(self, a0): #在 MainWindow 窗口被关闭时，确保执行父类 QMainWindow 的默认关闭行为。
        #self.refreshThread.mainProcess.terminate(force=True)
        super().closeEvent(a0)

    def info_button_press(self):#函数执行 iwconfig 命令并显示结果。
        self.stop_scan() #调用了 stop_scan 方法，通常用于停止当前正在进行的扫描过程。这可能包括终止扫描线程或停止更新 UI。
        self.textBrowser.show() #使得 textBrowser 这个控件可见。textBrowser用于显示文本信息的窗口部件。
        self.charView.hide()# 将 charView 和 ssid_charView 这两个控件隐藏起来。这样可以确保在显示 textBrowser 时，其他视图不会干扰用户的视线。
        self.ssid_charView.hide()
        #self.refreshThread.stop_update()
        process = subprocess.Popen("iwconfig", shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
                                   universal_newlines=True, bufsize=1)
        results = "" #初始化一个空字符串 results，用于存储 iwconfig 命令的输出结 
        for line in process.stdout.readlines():   #读取 iwconfig 命令的输出，每次读取一行，并将其添加到 results 字符串中。 
            results = results + line #这行代码将每一行输出附加到 results 字符串中。这样可以将所有输出行连接成一个完整的字符串。
        self.update_label(results) #调用 update_label 方法，将 results 中的内容显示在 textBrowser 上。更新 UI 以显示无线网络接口的配置信息。
    #执行了 iwconfig 命令，subprocess.Popen 方法启动了一个新的进程来运行这个命令，并将命令的标准输出和标准错误通过管道重定向，以便后续读取。
        # shell=True：在一个 shell 中执行命令。
        # stderr=subprocess.STDOUT：将标准错误重定向到标准输出，以便统一读取输出内容。
        # stdout=subprocess.PIPE：将标准输出重定向到一个管道，以便在 Python 中读取。
        # universal_newlines=True：将输出作为文本而不是字节读取。
        # bufsize=1：设置缓冲区大小为行缓冲模式。

    def scan_button_press(self):
        self.btn_scanbutton.setEnabled(False)#禁用了扫描按钮 (btn_scanbutton)，以防止在扫描过程中用户再次点击该按钮。这有助于避免重复的扫描请求。
        self.textBrowser.show()#使得 textBrowser 这个控件可见。textBrowser用于显示扫描结果或状态信息的窗口部件。
        self.charView.hide() #将 charView 和 ssid_charView 这两个控件隐藏起来。这样可以确保在显示 textBrowser 时，其他视图不会干扰用户的视线。
        self.ssid_charView.hide()
        self.is_scanning = True#将 is_scanning 标志设置为 True，表示正在进行扫描操作
        self.update_label("扫描中...")#调用 update_label 方法，向用户显示 "扫描中..." 的状态信息。更新 textBrowser 上的文本内容
        #self.refreshThread.stop_update()
        self.scanThread = ScanThread()#实例化了一个 ScanThread 对象
        self.scanThread.text.connect(self.update_label)#连接了 ScanThread 的 text 信号和 update_label 槽。text 信号会在扫描过程中发出，用于传递扫描结果或状态信息，update_label 槽则用于更新 UI 上的显示内容。
        self.scanThread.start()#启动了 ScanThread 线程，开始执行 WiFi 网络扫描操作。扫描过程将在后台进行，不会阻塞主线程，从而保持 UI 的响应性。

    def graphy_button_press(self):
        self.stop_scan()#调用了 stop_scan 方法，该方法通常用于停止正在进行的扫描操作。这有助于在切换视图之前确保没有后台扫描线程在运行。
        self.textBrowser.hide()#隐藏 textBrowser 控件。这通常用于显示扫描结果或状态信息，但在显示图形视图时不需要。
        self.ssid_charView.hide()#隐藏 ssid_charView 控件
        self.charView.show()#显示 charView 控件,显示一般的 WiFi 信号强度图形

    def ssid_graphy_button_press(self):
        self.stop_scan()
        self.textBrowser.hide()
        self.charView.hide()#隐藏 charView 控件
        self.ssid_charView.show()#显示 ssid_charView 控件，显示特定 SSID 的信号强度图形

    def about_button_press(self):# 显示关于窗口的信息
        self.stop_scan() #调用了 stop_scan 方法，用于停止当前进行的任何扫描操作。这确保在显示关于窗口的信息时，不会有后台扫描操作进行干扰。
        self.textBrowser.show()#显示 textBrowser 控件。textBrowser 控件通常用于显示文本信息，此处用于显示 "About" 信息。
        self.charView.hide()#隐藏wifi信号图
        self.ssid_charView.hide()#隐藏ssid信号图
        #self.refreshThread.stop_update() #停止刷新线程的更新
        about_text = """                                                                   status monitor for wireless network devices 
                                                                         By percyHou <xiagelearn@gmail.com>                                                                          
                                        A part of future's research<Muti-drone Communication Planning and Exploration"""
        self.update_label(about_text)#调用了 update_label 方法，将 about_text 的内容更新到 textBrowser 控件中，以显示关于窗口的信息。

    # def quit_button_press(self):
    #     self.close()

    def update_label(self, content: str):
        scroll_value = self.textBrowser.verticalScrollBar().value()#获取 textBrowser 控件的垂直滚动条当前的位置。这一步是为了在更新文本内容后保持滚动条的位置不变。
        self.textBrowser.setText(content)#将 textBrowser 控件的文本内容设置为传入的 content。这会用新的内容替换当前显示的文本。
        self.textBrowser.verticalScrollBar().setValue(scroll_value)#将 textBrowser 控件的垂直滚动条的位置设置为之前保存的位置。这样可以确保在更新文本内容后，滚动条的位置不会改变

    def scanningComplete(self, text):
        self.is_scanning = False#设置类的属性 is_scanning 为 False，表示扫描操作已经完成。
        self.update_label(text)#调用 update_label 方法，将传入的 text 更新到 textBrowser 控件中。

    def change_other_button(self, allow:bool):
        self.btn_infobutton.setEnabled(allow)#设置 btn_infobutton 按钮的启用状态为 allow。True 表示按钮可用，False 表示按钮不可用。
        self.btn_graphybutton.setEnabled(allow)#设置 btn_graphybutton 按钮的启用状态为 allow
        self.btn_scanbutton.setEnabled(allow)#设置 btn_scanbutton 按钮的启用状态为 allow。
        self.about_button.setEnabled(allow)#设置 about_button 按钮的启用状态为 allow。

    def update_chart(self):
        if len(level_data) > 0:#确保在 level_data 列表中有数据可供处理。如果列表为空，则不进行任何操作。
            mutex.lock()#mutex.lock() 用于在访问共享资源（level_data 列表）时避免竞态条件（race condition）。这确保了在操作 level_data 列表时，其他线程不会同时修改它。
            level_value = level_data[0]#获取 level_data 列表中的第一个数据点，并将其存储在 level_value 变量中。
            level_data.pop(0)#从 level_data 列表中删除该数据点。
            mutex.unlock()#解锁 mutex，允许其他线程访问 level_data 列表。
            if len(self._1_point_list) > 10:#如果 _1_point_list 列表中的点超过 10 个，则删除最旧的点（列表中的最后一个点）。这一步确保图表上只显示最新的 10 个数据点。
                del self._1_point_list[len(self._1_point_list) - 1]
            self._1_point_list.insert(0, QPointF(0, level_value))#创建一个新的 QPointF 对象，将其 x 值设置为 0，y 值设置为 level_value。然后将这个新的数据点插入到 _1_point_list 的开头。
            for i in range(0, len(self._1_point_list)):
                self._1_point_list[i].setX(i)#遍历 _1_point_list 列表中的所有点，并将它们的x 值设置为它们在列表中的索引。这一步确保每个点在图表中的位置是按时间顺序排列的。
            self.series_1.replace(self._1_point_list)#将 series_1 的数据替换为更新后的 _1_point_list。series_1 是一个 QLineSeries 对象，代表图表中的一条折线。replace 方法会用新的点数据替换当前的点数据，从而更新图表的显示。

    def update_ssid_chart(self):
        ssid_mutex.lock()#锁定 ssid_mutex 以确保线程安全

        is_valid = False    # 判断此次循环是否有数据

        if len(around_ssid_level_dict) > 0:#如果 around_ssid_level_dict 包含数据，则进入循环处理每个 SSID 的信号强度数据。
            for ssid, level_list in around_ssid_level_dict.items():
                if ssid not in self.series_ssids_dict.keys():#检查 series_ssids_dict 字典中是否已经存在当前的 SSID；series_ssids_dict 用于存储每个 SSID 及其对应的信号强度曲线和数据点列表。
#如果当前 SSID 不在 series_ssids_dict 中，表示这是一个新的 SSID，需要为其创建新的数据结构和图表表示。
                    new_line = QLineSeries()#创建一个新的 QLineSeries 对象，用于表示该 SSID 的信号强度曲线。
                    new_line.setName(ssid)#设置新创建的 QLineSeries 对象的名称为当前 SSID。显示在图表的图例中，便于识别不同的 SSID 曲线
                    self.ssid_charView.chart().addSeries(new_line)#将新创建的 QLineSeries 对象添加到图表中进行显示。ssid_charView 是显示 SSID 信号强度的图表视图，chart() 方法返回图表对象。
                    new_line.attachAxis(self.ssid_y_Aix)#将新创建的 QLineSeries 对象附加到图表的 y 轴和 x 轴上。
                    new_line.attachAxis(self.ssid_x_Aix)#ssid_y_Aix 和 ssid_x_Aix 分别表示 y 轴和 x 轴对象。通过附加坐标轴，确保新曲线能够正确显示在图表中，并随坐标轴的变化进行更新

                    tmp_list = []#创建一个新的空列表 tmp_list，用于存储该 SSID 的信号强度数据点。
                    self.series_ssids_dict[ssid] = {new_line: tmp_list}#在 series_ssids_dict 字典中添加新的条目，键是当前 SSID，值是一个包含 QLineSeries 对象和数据点列表的字典。

                if len(level_list) > 0:#判断是否包含数据点
                    is_valid = True
                    ssid_dict_lock.acquire()#使用 ssid_dict_lock 锁住 level_list，确保线程安全。
                    level_value = level_list[0]#获取 level_list 中的第一个数据点 level_value
                    level_list.pop(0)#从 level_list 中移除已获取的数据点。
                    ssid_dict_lock.release()#释放锁 ssid_dict_lock。

                    point_list = list(self.series_ssids_dict[ssid].values())[0]#从 series_ssids_dict 中获取当前 SSID 对应的数据点列表 point_list。
                    if len(point_list) > 10:#如果 point_list 的长度超过 10，则删除最旧的一个数据点，确保 point_list 的长度不超过 10。
                        del point_list[len(point_list) - 1]
                    point_list.insert(0, QPointF(0, level_value))#在 point_list 的开头插入新的数据点 QPointF(0, level_value)，其中 QPointF 是一个二维点，0 表示 x 轴坐标，level_value 表示 y 轴坐标。
                    for i in range(0, len(point_list)):#遍历 point_list，将每个数据点的 x 轴坐标设置为其索引值 i，确保数据点按时间顺序排列。
                        point_list[i].setX(i)
                    list(self.series_ssids_dict[ssid].keys())[0].replace(point_list)#将更新后的 point_list 替换到对应的 QLineSeries 对象中，以更新图表中的曲线。
            if is_valid:#如果 is_valid 为 True，表示在之前的循环中已经有数据被处理，因此需要继续执行下面的逻辑。更新表格右移
                for ssid in list(self.series_ssids_dict.keys()):#遍历 self.series_ssids_dict 中所有的 SSID。
                    if ssid not in around_ssid_level_dict:#如果当前 SSID 不在 around_ssid_level_dict 中，表示这个 SSID 没有新的信号数据，需要将其数据点的 x 轴坐标向右移动。
                        point_list = list(self.series_ssids_dict[ssid].values())[0]#从 self.series_ssids_dict 中获取当前 SSID 对应的数据点列表 point_list。
                        for i in range(0, len(point_list)):#遍历 point_list，将每个数据点的 x 轴坐标增加 1，使其向右移动一个位置。
                            point_list[i].setX(point_list[i].x() + 1)
                        list(self.series_ssids_dict[ssid].keys())[0].replace(point_list)#将更新后的 point_list 替换到对应的 QLineSeries 对象中，以更新图表中的曲线。
        # for ssid in list(self.series_ssids_dict.keys()):
        #     if ssid not in list(around_ssid_level_dict.keys()):
        #         self.ssid_charView.chart().removeSeries(list(self.series_ssids_dict[ssid].keys())[0])
        #         self.series_ssids_dict.pop(ssid)
        #         print("ssid {} is removed".format(ssid))

        ssid_mutex.unlock()#释放 ssid_mutex 锁
#
    def stop_scan(self):#定义一个名为 stop_scan 的方法，用于停止 WiFi 扫描操作。
        if self.scanThread:#检查当前对象是否存在 scanThread 实例
            self.scanThread.stop_scanning()#如果 scanThread 实例存在，调用该实例的 stop_scanning 方法，以停止扫描线程的执行。
        self.btn_scanbutton.setEnabled(True)#将扫描按钮 (btn_scanbutton) 重新启用，以允许用户再次点击进行扫描操作。


def remove_ansi_codes(s):#移除字符串中的 ANSI 转义码，该函数接受一个字符串 s 作为输入，并返回移除了 ANSI 转义码的字符串。
    # 在该正则表达式中添加 \x1B\x28\x42 项以匹配 0x1B 0x28 0x42 字节序列（ESC( B）
    ansi_escape = re.compile(r'(\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|\x1B\x28\x42)')
    return ansi_escape.sub('', s)#使用正则表达式 ansi_escape 查找字符串 s 中的所有匹配项，并将其替换为空字符串，从而移除所有的 ANSI 转义码。sub 方法将匹配的 ANSI 转义码替换为空字符串，返回处理后的字符串。
#这一行定义了一个正则表达式，用于匹配 ANSI 转义码。ANSI 转义码通常用于终端中的文本样式（例如颜色、粗体、下划线等），这些码通常以 ESC 字符 (\x1B) 开头。
#\x1B: 匹配 ESC 字符。
#(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]): 非捕获组，用于匹配不同类型的 ANSI 转义码。
#[@-Z\\-_]: 匹配单个字符，可以是 @ 到 Z、\、- 或 _。
#\[[0-?]*[ -/]*[@-~]: 匹配以 [ 开头，包含一些可选字符，后跟一个范围在 @ 到 ~ 之间的字符。
#|\x1B\x28\x42: 额外匹配的字节序列 \x1B\x28\x42，这是 ESC( B 的字节表示。


class ScanThread(QThread):#类继承自 QThread，用于创建一个独立线程执行 WiFi 扫描任务。
    text = pyqtSignal(str)#定义一个 pyqtSignal 类型的信号 text，用于在线程中发射扫描结果（字符串形式）。

    def __init__(self, ):#调用父类 QThread 的初始化函数。
        super().__init__()
        self.is_scanning = True#初始化一个布尔变量 is_scanning，用于控制扫描过程的进行。

    def run(self):
        while self.is_scanning:
            process = subprocess.Popen("nmcli -p device wifi", shell=True, stderr=subprocess.STDOUT,
                                       stdout=subprocess.PIPE,
                                       universal_newlines=True, bufsize=1)
            self.text.emit(process.stdout.read())#读取命令输出并通过 text 信号发射。
            time.sleep(3)#线程休眠 3 秒，然后继续循环。
#使用 subprocess.Popen 执行 nmcli -p device wifi 命令获取 WiFi 网络信息。
# shell=True：在 shell 中执行命令。
# stderr=subprocess.STDOUT：将标准错误重定向到标准输出。
# stdout=subprocess.PIPE：捕获标准输出。
# universal_newlines=True：启用文本模式（行分隔符）。
# bufsize=1：行缓冲模式。
    def stop_scanning(self):#设置 is_scanning 为 False，终止扫描循环。
        self.is_scanning = False


class DataThread(QThread):#继承自 QThread，用于创建一个独立线程持续获取 WiFi 信号强度数据。
    def __init__(self):#调用父类 QThread 的初始化函数。初始化 DataThread 对象，无需额外参数或初始化逻辑。
        super().__init__()

    def run(self):
        while True:

            data = get_wifi_signal_level()#调用 get_wifi_signal_level 函数获取当前的 WiFi 信号强度数据。
            if data:#如果成功获取到数据（data 不为 None）
                mutex.lock()#加锁，确保 level_data 的线程安全。
                level_data.append(data)#将获取到的信号强度数据添加到 level_data 列表中。
                mutex.unlock()#解锁
            time.sleep(1)#线程休眠 1 秒，然后继续下一次循环。


class SSID_DataThread(QThread):#类继承自 QThread，用于创建一个独立线程持续获取周围 WiFi 信号强度数据。
    def __init__(self):
        super().__init__()

    def run(self):
        while True:

            data_dict = get_around_ssid_signal_level()#调用 get_around_ssid_signal_level 函数获取当前周围 SSID 信号强度数据，返回一个字典。
            if data_dict:#如果成功获取到数据字典
                ssid_dict_lock.acquire()#加锁，确保 around_ssid_level_dict 的线程安全。保护了整个操作过程，防止其他线程在操作期间进入相同的代码块。
                ssid_mutex.lock()#确保对 around_ssid_level_dict 的具体操作是原子的。确保对 around_ssid_level_dict 的具体操作是原子的。
                for ssid, level in data_dict.items():#遍历数据字典中的所有 SSID 和对应的信号强度。
                    if ssid not in around_ssid_level_dict.keys():#如果 SSID 不在全局字典 around_ssid_level_dict 中。
                        around_ssid_level_dict[ssid] = [level]#将 SSID 和对应的信号强度列表添加到字典中。
                    else:#如果 SSID 已经在全局字典中。
                        around_ssid_level_dict[ssid].append(level)#将新的信号强度值追加到对应的列表中。
                for ssid in list(around_ssid_level_dict.keys()):#遍历全局字典中的所有 SSID。
                    if ssid not in list(data_dict.keys()):#如果 SSID 不在获取到的数据字典中。
                        around_ssid_level_dict.pop(ssid)#从全局字典中移除该 SSID。
                ssid_mutex.unlock()#解锁
                ssid_dict_lock.release()#释放锁
            time.sleep(1)#线程休眠 1 秒，然后继续下一次循环。

