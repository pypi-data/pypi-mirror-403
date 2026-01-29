import time
import pyautogui # 0.9.54
import pyperclip

class AutoGui:
    def __init__(self):pass
    @classmethod
    def write_ch(self,word,SleepTime = 1):
        '''
        输入文字
        :param word:
        :param SleepTime:
        :return:
        '''
        # 将中文复制到剪贴板
        pyperclip.copy(word)
        time.sleep(SleepTime)
        # 模拟按下Ctrl+V粘贴
        pyautogui.hotkey('Ctrl', 'V')
    @classmethod
    def enter(cls):
        pyautogui.press('Enter')