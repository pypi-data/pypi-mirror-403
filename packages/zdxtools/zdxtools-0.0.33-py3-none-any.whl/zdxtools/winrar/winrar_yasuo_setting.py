# winrar 路径
winrarpath = 'C:\Program Files\WinRAR\WinRAR.exe'

# 分卷大小
fenjuansize = '2g -v4g'

# 修复BUG的模式
fenjuansize_bug = 1024 * 1024 * 2

# 输出模式 ，如果为1直接输出到文件的当前文件夹，为0则是outinput_path 的路径
outmethod = 1

# 压缩完之后是否删除附件文件
yasuo_after_delet = True
# 压缩文件输出路径
# outinput_path = None

# 随机生成文件，防止压缩包md5相同
suijishu = False

#comment路径文件
zijieya_text = ''


#压缩密码
password_dq = ''


# 要额外附加的宣传文件
# other_add_file = [
#     r'F:\python\pyqt5\tools\fujia\更多游戏下载.url',
#
# ]


other_add_file = [
    r'F:\python\pyqt5\manager\winrar_yasuo\fujia\更多游戏下载.url',
]
other_add_file1 = [
    r'F:\python\pyqt5\manager\winrar_yasuo\path\更多人物卡下载.url',
]



# 爱尚游戏库
aisData = {'comfilepath': 'comment.txt',
           'add_file': other_add_file,
           'password': 'www.aisgame.xyz'}

CardData = {'comfilepath': 'comment_card.txt',
            'add_file': other_add_file1,
            'password': ''}

# 自解压选择-- 需要将data 配置文件放到这里
zijieya_setting = [
    aisData,
    CardData
]


if __name__ == '__main__':
    import os

    print(os.path.dirname(other_add_file[0]))
