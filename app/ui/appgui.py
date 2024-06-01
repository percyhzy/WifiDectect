
import random

from PyQt6 import QtCore, QtGui, QtWidgets

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QKeySequence


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):#创建并命名 MainWindow 对象，并设置其大小。
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1024, 512)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")#创建一个中央窗口部件并设置一个水平布局
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.vlayout = QtWidgets.QVBoxLayout(self.centralwidget)

        #创建多个按钮（如 btn_infobutton, btn_graphybutton, btn_ssid_button, btn_scanbutton, about_button），为其设置快捷键，并将其添加到垂直布局中。
        self.btn_infobutton = QtWidgets.QPushButton()
        self.btn_infobutton.setShortcut(QKeySequence("Ctrl+A"))
        self.btn_infobutton.setObjectName("btn_infobutton")

        self.vlayout.addWidget(self.btn_infobutton)

        self.btn_graphybutton = QtWidgets.QPushButton()
        self.btn_graphybutton.setShortcut(QKeySequence(Qt.Key.Key_F2))
        self.btn_graphybutton.setObjectName("btn_graphybutton")
        self.vlayout.addWidget(self.btn_graphybutton)

        self.btn_ssid_button = QtWidgets.QPushButton()
        self.btn_ssid_button.setShortcut(QKeySequence(Qt.Key.Key_F3))
        self.btn_ssid_button.setObjectName("btn_ssid_button")
        self.vlayout.addWidget(self.btn_ssid_button)

        self.btn_scanbutton = QtWidgets.QPushButton()
        self.btn_scanbutton.setShortcut(QKeySequence(Qt.Key.Key_F4))
        self.btn_scanbutton.setObjectName("btn_scanbutton")
        self.vlayout.addWidget(self.btn_scanbutton)

        self.about_button = QtWidgets.QPushButton()
        self.about_button.setShortcut(QKeySequence(Qt.Key.Key_F5))
        self.about_button.setObjectName("about_button")
        self.vlayout.addWidget(self.about_button)

        # self.btn_quitbutton = QtWidgets.QPushButton()
        # self.btn_quitbutton.setObjectName("btn_quitbutton")
        # self.vlayout.addWidget(self.btn_quitbutton)

        self.vlayout.addStretch()

        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)#文本浏览器：创建一个文本浏览器用于显示文本信息。
        self.horizontalLayout.addLayout(self.vlayout)

        #初始化两个图表（charView 和 ssid_charView）用于显示 WiFi 和 SSID 信号强度。这些图表初始时被隐藏，并被添加到水平布局中。
        self.init_line()
        self.init_ssid_line()
        self.init_wifi_chart()
        self.init_ssid_chart()
        self.charView.hide()
        self.ssid_charView.hide()
        self.horizontalLayout.addWidget(self.charView)
        self.horizontalLayout.addWidget(self.ssid_charView)

        self.horizontalLayout.addWidget(self.textBrowser)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)#菜单和状态栏：创建并设置菜单栏和状态栏。
        self.menubar.setGeometry(QtCore.QRect(0, 0, 198, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)#处理 UI 元素的翻译和槽连接。
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):#这个方法为各种 UI 元素设置文本
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "percyWifi"))
        self.btn_infobutton.setText(_translate("MainWindow", "网卡信息"))
        self.btn_graphybutton.setText(_translate("MainWindow", "WIFI功率折线图"))
        self.btn_ssid_button.setText(_translate("MainWindow", "SSID信号强度折线图"))
        self.btn_scanbutton.setText(_translate("MainWindow", "扫描"))
        self.about_button.setText(_translate("MainWindow", "关于此程序"))
        # self.btn_quitbutton.setText(_translate("MainWindow", "退出"))

    #初始化用于 WiFi 功率折线图的点列表。
    def init_line(self):
        self._1_point_list = []
        for i in range(10):
             y = -10
             self._1_point_list.append(QPointF(i, y))

        self.series_1 = QLineSeries()
        self.series_1.setName("WIFI功率折线")

    #初始化 SSID 折线：初始化一个空字典，用于存储 SSID 的系列。
    def init_ssid_line(self):
        self.series_ssids_dict = {}

    #初始化 WiFi 图表：配置 x 轴和 y 轴，并将系列添加到图表视图中。
    def init_wifi_chart(self):
        # 设置x轴
        self.x_Aix = QValueAxis()
        self.x_Aix.setRange(0.00, 10.00)
        self.x_Aix.setLabelFormat("%0.2f")
        self.x_Aix.setTitleText("时间（秒）")
        self.x_Aix.setTickCount(11)
        self.x_Aix.setMinorTickCount(4)

        # 设置y轴
        self.y_Aix = QValueAxis()
        self.y_Aix.setTitleText("功率（dBm）")
        self.y_Aix.setRange(-100.00, -10.00)
        self.y_Aix.setLabelFormat("%0.2f")
        self.y_Aix.setTickCount(6)
        self.y_Aix.setMinorTickCount(4)

        self.charView = QChartView(self)


        self.charView.chart().addSeries(self.series_1)

        self.charView.chart().addAxis(self.x_Aix, Qt.AlignmentFlag.AlignBottom)
        self.charView.chart().addAxis(self.y_Aix, Qt.AlignmentFlag.AlignLeft)

        self.series_1.attachAxis(self.y_Aix)
        self.series_1.attachAxis(self.x_Aix)

    #初始化 SSID 图表：类似于 WiFi 图表的配置，但用于显示 SSID 信号强度。
    def init_ssid_chart(self):
        self.ssid_x_Aix = QValueAxis()
        self.ssid_x_Aix.setRange(0.00, 10.00)
        self.ssid_x_Aix.setLabelFormat("%0.2f")
        self.ssid_x_Aix.setTitleText("扫描（次）")
        self.ssid_x_Aix.setTickCount(11)
        self.ssid_x_Aix.setMinorTickCount(4)

        # 设置y轴
        self.ssid_y_Aix = QValueAxis()
        self.ssid_y_Aix.setTitleText("功率（dBm）")
        self.ssid_y_Aix.setRange(-100.00, -10.00)
        self.ssid_y_Aix.setLabelFormat("%0.2f")
        self.ssid_y_Aix.setTickCount(6)
        self.ssid_y_Aix.setMinorTickCount(4)

        self.ssid_charView = QChartView(self)

        self.ssid_charView.chart().addAxis(self.ssid_x_Aix, Qt.AlignmentFlag.AlignBottom)
        self.ssid_charView.chart().addAxis(self.ssid_y_Aix, Qt.AlignmentFlag.AlignLeft)

