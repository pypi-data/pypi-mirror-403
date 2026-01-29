# 图像封装
import os

class dx_img:
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
    # png转jpg
    @classmethod
    def png_jpg(cls, picpath, fold=False):
        from PIL import Image
        '''

        :param picpath: 要转换的图片
        :param fold: 是否需要放到新的文件夹，默认是当前地址
        :return: 成功返回新的地址  失败返回false
        '''
        img = Image.open(picpath)
        if not fold:
            newpath = os.path.join(os.path.dirname(picpath), f'''{cls.get_wuhouzhuifilename(picpath)}.jpg''')
        else:
            newpath = os.path.join(fold, f'''{cls.get_wuhouzhuifilename(picpath)}.jpg''')

        try:
            img.save(newpath)
            return newpath
        except:
            try:
                img = img.convert('RGB')  # 1是以彩色图方式去读
                # 存放虚假展示图片
                img.save(newpath)

                print(picpath, '转换成功！')
                # 返回文件名
                return newpath
            except Exception as e:
                print(e)
                return False

    @classmethod
    def change_md5(cls, picpath):
        '''
        修改图片md5
        :param picpath:
        :return:
        '''
        import time
        writefile = int(time.time() * 1000)
        with open(picpath, "a") as f:
            f.write(str(writefile))