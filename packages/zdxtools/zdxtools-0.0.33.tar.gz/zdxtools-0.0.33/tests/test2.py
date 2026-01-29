from pypi_update.src.zdxtools.dx_tools import dx_os


dx_os.move(oldPath=r'C:\Users\10571\Desktop\浏览器\新建文件夹\creidOvO_8987.lnk',newdir=r'C:\Users\10571\Desktop\浏览器\新建文件夹\新建文件夹',delete=True)


# 最终推荐函数
def contains_ignore_case(text, substring, use_casefold=True):
    """
    不区分大小写的字符串包含检查
    支持中英文混合字符串

    Args:
        text: 主字符串
        substring: 要查找的子字符串
        use_casefold: 是否使用 casefold (推荐 True)

    Returns:
        bool: 是否包含
    """
    if use_casefold:
        return substring.casefold() in text.casefold()
    else:
        return substring.lower() in text.lower()


# 使用
text = "欢迎使用PYTHON22编程"
print(contains_ignore_case(text, "python"))  # True
print(contains_ignore_case(text, "python编程"))  # True