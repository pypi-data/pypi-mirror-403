# -*- coding: utf-8 -*-
import os
import sys
if not os.path.exists('winrar_yasuo_setting.py'):
    base_file = ['winrar_yasuo_setting.py','comment.txt','comment_card.txt']
    for i in base_file:
        yuan_file = os.path.join(os.path.dirname(__file__),i)
        with open (yuan_file ,mode='rb')as f :
            data = f.read()
        new_file = os.path.join(os.getcwd(),i)
        with open (new_file ,mode='wb')as f :
            f.write(data)
    print('winrar 批量压缩，缺少配置文件，已生成在当前运行目录，请配置好后再运行')
    exit()
# sys.path.append(os.path.dirname(__file__))
import subprocess
import re
import time
from shutil import copy,move,rmtree
import winrar_yasuo_setting as setting
# sys.path.remove(os.path.dirname(__file__))
'''
winrar a -v1m -sfx  -z"comment.txt" test1 test2 -p123456zxc
r"C:\\Program Files\\WinRAR\\WinRAR.exe " a -ap"原神 - 派蒙" -v2g -v4g -sfx  -z"comment_card.txt" "原神 - 派蒙" "E:\\software下载包\\card1\\原神 - 派蒙.png"  -ep1
'''
#支持文件
class zuj:
    @classmethod
    def path_qx(cls,path):
        return path.replace('\\\\','\\')
    @classmethod
    def get_ping(cls,ip, count):
        platform = sys.platform

        if "win" in platform:
            command = 'ping -n %s' % count + " %s" % ip
            p = subprocess.Popen(command,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
            out = p.stdout.read().decode('gbk')
            # regex = r'时间=(.+?)ms'

        elif "linux" in platform:
            command = 'ping -c %s' % count + " %s" % ip
            p = subprocess.Popen([command],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
            out = p.stdout.read().decode('utf-8')
            # regex = r'time=(.+?)ms'

        print(out)
    # 获得文档里支持的setup 对应的url
    @classmethod
    def get_url(cls, path):
        with open(path) as f:
            c = f.readlines()
            for i in c:
                if 'Setup' in i:
                    return i.split('=')[1].replace('\n','')
    #生成随机文件
    @classmethod
    def make_radom_file(cls,path):
        '''

        :param path: 生成随机文件，返回生成的随机文件地址
        :return:
        '''
        newpath = os.path.join(path, str(time.time()))
        with open(newpath, mode='w') as f:
            f.write(str(time.time()))
        return  newpath
    # 获得文件夹大小
    @classmethod
    def get_true_size(cls,path):

        if os.path.isdir(path):
            size = 0
            pathlist = [i for i in os.walk(path)]
            for i in pathlist:
                for f in i[2]:
                    size += os.path.getsize(os.path.join(i[0], f))
        else:
            size = os.path.getsize(path)
        return size
    @classmethod
    def choice_zijieya_text(cls,f):
        if setting.zijieya_setting:
            n = 1
            print('请选择默认要打开的网址')
            for i in setting.zijieya_setting:
                newpath = i['comfilepath']
                print(f'''{n} {zuj.get_url(newpath)}''')
                n += 1
            choice = int(input('请输入编号：'))-1
            peizhi = setting.zijieya_setting[choice]
            add_file = peizhi.get('add_file','')
            password = peizhi.get('password','')
            if add_file:
                setting.other_add_file = add_file
            #配置密码
            if password:
                setting.password_dq = password
            setting.zijieya_text = peizhi['comfilepath']

        def inner(*args, **kwargs):  # *代表聚合
            ret = f(*args, **kwargs)  # *代表打散
            return ret
        return inner
    #获得密码
    @classmethod
    def getpassword(self):
        return f'''-p{setting.password_dq}''' if hasattr(setting,'password_dq') else ''


#压缩模式1，针对文件夹先添加附加文件再压缩
def winrar_plyasuo1(path):
    '''
    1.输入文件夹path，会把附带文件夹加入这个文件夹里【推荐】
    2.输入单个文件,会以文件名，创建一个文件夹，附加文件会装入这个文件夹
    其它配置文件在setting里配置
    对于2G 以上大小的  会出现BUG
    :param path:
    :return:
    '''
    #如果是文件夹直接把附加文件添加进文件夹
    rm_file_list = []
    if os.path.isdir(path):
        for i in setting.other_add_file:
            copy(i,path)
            rm_file_list.append(os.path.join(path,os.path.basename(i)))
    else:
        for i in setting.other_add_file:
            copy(i,os.path.dirname(path))
            rm_file_list.append(os.path.join(os.path.dirname(path),os.path.basename(i)))
    #生成随机文件
    if hasattr(setting,'suijishu') :
        if setting.suijishu :
            rad_path = zuj.make_radom_file(path)
            rm_file_list.append(rad_path)
    #默认输出文件
    if setting.outmethod == 0:
        outpath =setting.outinput_path if hasattr(setting,'outinput_path') else os.path.join(os.getcwd(),
                                                                                             '../../tools/out')
    else :
        outpath = os.path.dirname(path)

    if not os.path.exists(outpath):
        os.makedirs(outpath)
    if not os.path.exists(path):
        return False

    #密码选项
    password = zuj.getpassword()

    #开始压缩
    if os.path.isdir(path):
        outname = os.path.join(outpath,os.path.basename(path))+'.exe'
        if os.path.exists(outname):
            print(f'{outname} 文件重复')
            return
        # outname = os.path.basename(path)
        command = f'''"{setting.winrarpath}" a -v{setting.fenjuansize} -sfx  -z"{setting.zijieya_text}" "{outname}" "{path}" {password} -ep1'''
    else:
        basename = os.path.basename(path).split('.')[0]
        outname = os.path.join(outpath,basename)+'.exe'
        if os.path.exists(outname):
            print(f'{outname} 文件重复')
            return
        # outname = basename
        command = f'''"{setting.winrarpath}" a  -v{setting.fenjuansize} -sfx  -z"{setting.zijieya_text}" "{outname}" "{os.path.dirname(path)}" {password} -ep1'''

    proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE,encoding='GBK')
    print(proc)
    time.sleep(3)
    #压缩完之后删除
    if  setting.yasuo_after_delet :
        for i in rm_file_list:
            os.remove(i)

#压缩模式2，针对单个文件，先创建一个同名文件夹，再把文件移动进去，再压缩，压缩完了再把文件移动出来，再删除文件夹
new_dir_path_list = []
def winrar_plyasuo2(path):
    '''
    1.输入文件夹path，会把附带文件夹加入这个文件夹里【推荐】
    2.输入单个文件,会以文件名，创建一个文件夹，附加文件会装入这个文件夹
    其它配置文件在setting里配置
    对于2G 以上大小的  会出现BUG
    :param path:
    :return:
    '''
    #建同名文件夹
    houzhui = path.split('.')[-1]
    new_dir_path = path.replace(f'.{houzhui}','')
    if os.path.exists(new_dir_path):
        print('已存在')
        return
    else:
        os.mkdir(new_dir_path)

    #直接把附加文件添加进文件夹
    rm_file_list = []
    for i in setting.other_add_file:
        copy(i,new_dir_path)
        rm_file_list.append(os.path.join(new_dir_path,os.path.basename(i)))
    #再把文件移动进去
    try:
        move(path,new_dir_path)
    except:pass
    #生成随机文件
    if hasattr(setting,'suijishu') :
        if setting.suijishu :
            rad_path = zuj.make_radom_file(new_dir_path)
    #移动后的文件地址
    newpath = os.path.join(new_dir_path,os.path.basename(path))

    #默认输出文件
    if setting.outmethod == 0:
        outpath =setting.outinput_path if hasattr(setting,'outinput_path') else os.path.join(os.getcwd(),
                                                                                             '../../tools/out')
    else :
        outpath = os.path.dirname(path)

    if not os.path.exists(outpath):
        os.makedirs(outpath)

    #密码选项
    password = zuj.getpassword()

    #开始压缩
    basename = os.path.basename(new_dir_path)
    outname = os.path.join(outpath,basename)+'.exe'
    if os.path.exists(outname):
        print(f'{outname} 文件重复')
        return
    # outname = basename
    command = f'''"{setting.winrarpath}" a  -v{setting.fenjuansize} -sfx  -z"{setting.zijieya_text}" "{outname}" "{new_dir_path}" {password} -ep1'''

    proc = subprocess.run(command, shell=True, stdout=subprocess.PIPE)
    print(proc)

    # 再把文件移动进去
    move(newpath, os.path.dirname(path))

    # 删除单独创建的文件夹
    rmtree(new_dir_path)
    # new_dir_path_list.append(new_dir_path)

#启动程序
@zuj.choice_zijieya_text
def manager():
    while True:
        path = input('请输入要压缩的文件夹或者文件地址').strip('\u202a')
        if not os.path.isdir(path):
            winrar_plyasuo2(path)
            continue
        choice = input('压缩当前文件夹1 \n对文件夹里面的第一层分别压缩2 \n请选择:')
        if choice == '1':
                winrar_plyasuo1(path)
        elif choice == '2':
            filst = os.listdir(path)
            for i in filst:
                newpath = os.path.join(path,i)
                #如果是文件夹则走文件夹模式
                if os.path.isdir(newpath) :
                    winrar_plyasuo1(newpath)
                else:
                    #如果是文件则走压缩模式2
                    winrar_plyasuo2(newpath)
            # for i in new_dir_path_list:
            #     rmtree(i)
if __name__ == '__main__':
    #导入说明 from  zdxtools.winrar.winrar_yasuo import manager
    os.chdir(os.path.dirname(__file__))
    manager()





