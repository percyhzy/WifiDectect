import argparse #用于解析命令行参数
import sys #与Python解释器交互
import traceback #打印异常的堆栈跟踪



def new_excepthook(type, value, tb): #当程序发生未处理的异常时，将调用此函数。它使用 traceback.print_exception 来打印异常的详细信息，包括异常类型、值和回溯信息
    # by default, Qt does not seem to output any errors, this prevents that
    traceback.print_exception(type, value, tb)


sys.excepthook = new_excepthook #设置为全局异常处理函数 


def main():
    parser = argparse.ArgumentParser() #创建一个参数解析器对象。
    parser.add_argument('--no-gui', action='store_true') #添加一个命令行选项 --no-gui，它是一个布尔标志，如果在命令行中出现，将设置为 True。
    args = parser.parse_args() #解析命令行参数并返回一个包含参数值的命名空间对象 args。

    from PyQt6.QtWidgets import QApplication #导入 PyQt6 的 QApplication 类。
    from .gui import MainWindow #从本地模块 gui 导入 MainWindow 类。
    qapp = QApplication(sys.argv) #创建一个 QApplication 实例，并传递命令行参数 sys.argv。
    gui = MainWindow()#创建 MainWindow 类的实例，表示主窗口。
    gui.show()#显示主窗口
    sys.exit(qapp.exec())#启动 Qt 事件循环，并在程序结束时退出。


if __name__ == '__main__':
    main() #确保只有在直接运行脚本时才会调用 main 函数  
