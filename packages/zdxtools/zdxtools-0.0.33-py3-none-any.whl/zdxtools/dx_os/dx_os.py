#os的封装
import os
import shutil
import uuid


class dx_os:
    def __init__(self):pass

    #获得无后缀的文件名
    @classmethod
    def get_wuhouzhuifilename(cls,path):
        '''
        :param path: 传入路径
        :return:
        '''
        import os
        title_1ist = os.path.basename(path).split('.')
        if len(title_1ist) > 1:  # 去掉后缀
            title_1ist.pop(-1)
            title = ''.join(title_1ist)
        else:
            title = os.path.basename(path)
        return title
    #获得文件后缀
    @classmethod
    def get_file_houzhui(cls,path):
        '''
        :param path: 传入路径
        :return:
        '''
        import os
        houzhui  = path.split('.')[-1]
        return houzhui
    #获得可保存的无特殊符号的文件名
    @classmethod
    def get_chunjingfilename(cls,file):
        ts = ['?',r'\n']
        for i in ts:
            file = file.replace(i,'')
        return file
    #获得文件夹内所有文件的绝对路径，返回列表
    @classmethod
    def get_fold_file_absolute(self,path,recursion = False):
        '''
        :param path:
        :param recursion: 递归，默认为FALSE
        :return:
        '''
        paths = os.walk(path)
        if not recursion:
            pathlist = [i for i in paths]
            newpathlist = [f'''{os.path.join(pathlist[0][0], i)}''' for i in pathlist[0][2]]
        else:
            newpathlist = [os.path.join(i[0], f) for i in paths for f in i[2]]
        return newpathlist
    @classmethod
    def get_all_folders(cls,path):
        """获取指定路径下所有文件夹（包含子文件夹）"""
        folders = []
        for root, dirs, files in os.walk(path):
            for dir_name in dirs:
                folder_path = os.path.join(root, dir_name)
                folders.append(folder_path)
        return folders
    #给文件随机重命名
    @classmethod
    def get_new_file_name(cls,filename,uuidFlag =False,DirReserve = False):
        '''

        :param filename:
        :param uuidFlag: 如果为True  那么 文件名会添加uuid4 的信息，更唯一
        :param DirReserve:保留目录 返回完整路径 + 新随机名称
        :return:
        '''
        import time
        if DirReserve:
            dirpath = os.path.dirname(filename)
        ext = filename.split('.')[-1]
        if not uuidFlag:
            filename = '{}.{}'.format(str(time.time()).split('.')[0], ext)
        else:
            filename = f'''{uuid.uuid4()}-'''+'{}.{}'.format(str(time.time()*100).split('.')[0], ext)
        if DirReserve:
            filename = os.path.join(dirpath, filename)
        return filename
    #移动单个文件
    @classmethod
    def move(cls,oldPath,newPath = False,newdir = False,delete = False):
        '''

        '''
        try:
            with open(oldPath, mode='rb') as f:
                data = f.read()
            if not newPath:
                newPath = os.path.join(newdir, os.path.basename(oldPath))
            with open(newPath, mode='wb') as f:
                f.write(data)
            if delete:
                os.remove(oldPath)
            return True
        except Exception as e:
            return False
    #移动文件夹
    @classmethod
    def copy_dir(cls,src_path, target_path,delete = False):
        if not os.path.exists(target_path):
            os.mkdir(target_path)
        if os.path.isdir(src_path) and os.path.isdir(target_path):
            filelist_src = os.listdir(src_path)
            for file in filelist_src:
                path = os.path.join(os.path.abspath(src_path), file)
                if os.path.isdir(path):
                    path1 = os.path.join(os.path.abspath(target_path), file)
                    if not os.path.exists(path1):
                        os.mkdir(path1)
                    cls.copy_dir(path, path1)
                else:
                    with open(path, 'rb') as read_stream:
                        contents = read_stream.read()
                        path1 = os.path.join(target_path, file)
                        with open(path1, 'wb') as write_stream:
                            write_stream.write(contents)
            if delete:
                shutil.rmtree(src_path)
            return True

        else:
            return False
    #设置快捷方式
    @classmethod
    def set_shortcut(cls,filename, lnkname, argumensts, startpath = '', iconname=''):  # 如无需特别设置图标，则可去掉iconname参数
        '''

        :param filename: 文件完整路径
        :param lnkname: 快捷方式存放路径
        :param argumensts: 参数 --user-data-dir=E:softwaregooglechromesgooglechrome4 多开
        :param startpath: 开始位置 [废弃，直接从 filename得到]
        :param iconname: 图标路径
        :return:
        '''
        import pythoncom
        from win32com.shell import shell
        from win32com.shell import shellcon
        try:
            # 将要在此路径创建快捷方式
            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink, None,
                pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
            shortcut.SetPath(filename)
            shortcut.SetArguments(argumensts)
            shortcut.SetWorkingDirectory(os.path.dirname(filename))  # 设置快捷方式的起始位置, 不然会出现找不到辅助文件的情况
            shortcut.SetIconLocation(iconname, 0)  # 可有可无，没有就默认使用文件本身的图标
            if os.path.splitext(lnkname)[-1] != '.lnk':
                lnkname += ".lnk"
            shortcut.QueryInterface(pythoncom.IID_IPersistFile).Save(lnkname, 0)
            return True
        except Exception as e:
            print(e.args)
            return False
    #设置快捷方式
    @classmethod
    def GetShortCut_path(cls,path):
        import struct
        target = ''
        try:
            with open(path, 'rb') as stream:
                content = stream.read()

                # skip first 20 bytes (HeaderSize and LinkCLSID)
                # read the LinkFlags structure (4 bytes)
                lflags = struct.unpack('I', content[0x14:0x18])[0]
                position = 0x18

                # if the HasLinkTargetIDList bit is set then skip the stored IDList
                # structure and header
                if (lflags & 0x01) == 1:
                    position = struct.unpack('H', content[0x4C:0x4E])[0] + 0x4E

                last_pos = position
                position += 0x04

                # get how long the file information is (LinkInfoSize)
                length = struct.unpack('I', content[last_pos:position])[0]

                # skip 12 bytes (LinkInfoHeaderSize, LinkInfoFlags, and VolumeIDOffset)
                position += 0x0C

                # go to the LocalBasePath position
                lbpos = struct.unpack('I', content[position:position + 0x04])[0]
                position = last_pos + lbpos

                # read the string at the given position of the determined length
                size = (length + last_pos) - position - 0x02
                temp = struct.unpack('c' * size, content[position:position + size])
                target = ''.join([chr(ord(a)) for a in temp])
        except:
            # could not read the file
            pass

        return target
    @classmethod
    def convert_size(cls,size: '字节数'):
        units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'BB', 'NB', 'DB', 'CB', 'XB', '?B']
        unit = units[0]
        for i in range(1, len(units)):
            if size > 1024:
                size /= 1024
                unit = units[i]
            else:
                break
            if unit == '?B':
                break

        size = float('%.2f' % size)
        return '%s %s' % (format(size, ','), unit)
    #path方面
    class path:
        #获得桌面路径
        @classmethod
        def get_desk_path(cls):
                return os.path.join(os.path.expanduser('~'), "Desktop")
        #判断是否是lnk文件
        @classmethod
        def is_link(cls,path):
            if path[-3:] == 'lnk':
                return True
            else:
                return False
        #获得目录下所有文件的路径，返回列表
        @classmethod
        def get_all_filepath(cls,path):
            '''
            获得目录下所有文件的路径，返回列表
            :param path:
            :return:
            '''
            path = path.replace('\u202a', '')
            pathwalk = [i for i in os.walk(path)]
            pathlist = []
            for i in pathwalk:
                for f in i[2]:
                    pathlist.append(os.path.join(i[0], f))
            return pathlist