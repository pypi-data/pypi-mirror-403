'''
以管理员方式运行
'''
import ctypes
import os
import sys
import subprocess
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin(func = False):
    '''
    :param func: 回调函数
    :return:
    '''
    if not is_admin():
        # 这里可以弹出提示，告诉用户需要以管理员身份运行
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        # 你的代码逻辑
        if func:
            func()
        # print("Running as admin.")


def run_as_vbs(file,encoding = 'ANSI'):
    '''

    :param file: 要以管理员模式执行的文件名，可以是全路径，如果是相对路径请放在运行目录下
    :return:
    '''
    content = f'''
    Set UAC = CreateObject("Shell.Application")  
    UAC.ShellExecute "{file}", "", "", "runas", 1
    '''
    vbsFilePath = 'run_as_vbs.vbs'
    with open(vbsFilePath ,mode='w',encoding=encoding) as f :
        f.write(content)
    result = subprocess.run([vbsFilePath], capture_output=True, shell=True,check=True)

    # 注意：主进程没有直接的方法来获取或设置其名称（除了sys.argv[0]）
if __name__ == '__main__':pass

    # test()