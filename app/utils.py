# coding:utf-8
import os#用于处理操作系统相关的功能，如文件路径操作。
import re#用于处理正则表达式
import subprocess#用于启动和与子进程进行交互
import sys#用于访问与 Python 解释器相关的变量和函数


def resource_path(relative=''):#该函数用于生成资源文件的绝对路径。relative：相对路径（默认为空字符串）
    root = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))#尝试获取 _MEIPASS 属性（如果存在），否则返回当前脚本目录的上一级目录的绝对路径。
    return os.path.join(root, 'app', 'data', relative)#将根路径与 'app/data/' 目录和相对路径组合成一个新的路径。

def get_wifi_signal_level():#用于获取当前 WiFi 信号的强度
    process = subprocess.Popen("iwconfig", shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
                               universal_newlines=True, bufsize=1)
    #使用 subprocess.Popen 启动 iwconfig 命令以获取 WiFi 信息。
    #shell=True：通过 shell 执行命令。
    #stderr=subprocess.STDOUT：将标准错误重定向到标准输出。
    #stdout=subprocess.PIPE：捕获标准输出。
    #universal_newlines=True：使用文本模式处理输入和输出。
    #bufsize=1：设置缓冲区大小为 1。

    result = re.search(r'Signal level=(.{3})', process.stdout.read(), re.IGNORECASE)#使用正则表达式匹配 Signal level 的值
    if result and len(result.groups()) > 0:#如果匹配到结果，并且结果组非空，则返回匹配到的信号强度值。
        #r'Signal level=(.{3})'：匹配 "Signal level=" 后跟随的任意三个字符。
        #re.IGNORECASE：忽略大小写。
        return int(result.groups()[0])
    return None#return None：如果未匹配到信号强度值，返回 None。


def get_around_ssid_signal_level():
    process = subprocess.Popen("iwlist scan", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)#启动 iwlist scan 命令来扫描周围的 WiFi 网络。
    #shell=True：通过 shell 执行命令。
    #stdout=subprocess.PIPE：捕获标准输出。
    #stderr=subprocess.STDOUT：将标准错误重定向到标准输出。
    ssid_dict = {}#用于存储 SSID 和对应的信号强度
    signal_level = None#用于暂存当前解析到的信号强度。
    for line in process.stdout.readlines():#逐行读取 iwlist scan 的输出，并进行必要的解码和清理。
        line = line.decode("unicode_escape").encode("latin1").decode("utf-8")#这一步将行内容从 unicode_escape 解码为 latin1，再解码为 utf-8，确保正确处理可能存在的转义字符。
        line = line.rstrip()#移除行尾的空白字符。

        signal_level_result = re.search(r'Signal level=(.{3})', line, re.IGNORECASE)
        #使用正则表达式匹配 Signal level 值，并暂存到 signal_level 变量中。
        #匹配 "Signal level=" 后跟随的任意三个字符，不区分大小写。
        if signal_level_result and len(signal_level_result.groups()) > 0:#如果匹配成功且有结果，则提取信号强度并去除末尾的空白字符。
            signal_level = signal_level_result.groups()[0].rstrip()#暂存信号强度值。
            continue#跳过本次循环的剩余部分，继续下一行

        #查找并提取 SSID（网络名称），并将其与之前提取的信号强度关联
        if "essid" in line.rstrip().lower():#如果行中包含 "essid" 字样（不区分大小写），则继续处理。
            essid = line.split(":")[1]#提取 SSID 名称（"essid:" 后的部分）
            if signal_level:#如果信号强度值已被提取，则将其与当前 SSID 关联
                ssid_dict[essid] = int(signal_level)#将 SSID 和信号强度以键值对形式存储在 ssid_dict 中。
                signal_level = None#重置信号强度变量，准备处理下一个网络
    return ssid_dict#返回一个字典，其中包含所有检测到的 SSID 及其对应的信号强度


if __name__ == "__main__":
    print(get_around_ssid_signal_level())




