#装饰器
import time
import traceback

from tqdm import tqdm


class decorator:
    #显示异常装饰器，很多时候有些过程无法显示异常内容，比方说pyqt5 ，所以说加个这个装饰器，就可以了
    @classmethod
    def ExceptionD(cls,f):
        def func_inner(*args, **kwargs):
            try:
                ret = f(*args, **kwargs)  # *代表打散
                return ret
            except Exception as E:
                print(E)

        return func_inner

    @classmethod
    def ExceptionD_desc(cls,f):
        def func_inner(*args, **kwargs):
            try:
                ret = f(*args, **kwargs)  # *代表打散
                return ret
            except Exception as E:
                traceback.print_exc()

        return func_inner

    @classmethod
    def ExceptionD_desc_sleep(cls,times = 1,*args,**kwargs):
        def func_out(f):
            def func_inner(*args, **kwargs):
                try:
                    ret = f(*args, **kwargs)  # *代表打散
                    return ret
                except Exception as E:
                    traceback.print_exc()
                    time.sleep(times)
            return func_inner
        return func_out

    @classmethod
    def Retry(cls,times = 3,sleeptime = 1,prints = True,printE = True,*args,**kwargs):
        '''
        函数重试尝试
        times: 失败重试次数
        sleeptime:尝试间隔时间
        prints:打印重试过程 默认为True
        printE:结束是否输入异常 默认为True
        '''
        def func_out(f):
            def func_inner(*args, **kwargs):
                failsNum = 0
                failFlag = True
                while failFlag :
                    try:
                        ret = f(*args, **kwargs)  # *代表打散
                        return ret
                    except Exception as E:
                        if failsNum < times:
                            failsNum += 1
                            if prints:
                                print(f'{f} 运行失败， 等待{sleeptime}秒后进行第{failsNum}次重试 ')
                            time.sleep(sleeptime)
                        else:
                            failFlag = False
                            if printE:
                                traceback.print_exc()
            return func_inner
        return func_out
    @classmethod
    def Test(cls,TestTimes = 1,ReTimes = 3,sleeptime = 0,prints = True,printE = False,*args,**kwargs):
        '''
        性能测试装饰器，目前是计算时间
        允许失败次数
        :prams TestTimes 测试次数
        :prams ReTimes 失败尝试次数
        :prams sleeptime 失败睡眠时间
        :prams prints 是否打印失败重试信息
        :prams printE 是否打印报错信息
        '''
        def func_out(f):
            def func_inner(*args, **kwargs):
                nonlocal TestTimes
                AllFailsNum = 0
                ret = False
                nowTime = time.time()
                TestTimes_ = TestTimes
                print(f'{f} 开始执行测试,本次测试次数{TestTimes}次')
                with tqdm(total=TestTimes_, desc=f'正在测试函数 {f}', leave=False, ncols=100, unit='次',
                          unit_scale=True) as pbar:
                    while TestTimes:
                        failsNum = 0
                        failFlag = True
                        while failFlag :
                            try:
                                ret = f(*args, **kwargs)  # *代表打散
                                TestTimes -= 1
                                pbar.update(1)
                                failFlag = False
                            except Exception as E:
                                if failsNum < ReTimes:#3
                                    failsNum += 1
                                    if prints:
                                        print(f'{f} 运行失败， 等待{sleeptime}秒后进行第{failsNum}次重试 ')
                                    time.sleep(sleeptime)
                                else:
                                    failFlag = False
                                    TestTimes -= 1
                                    pbar.update(1)
                                    if printE:
                                        traceback.print_exc()

                                AllFailsNum+=1

                FullTime = round((time.time() - nowTime), 4)
                print(f'运行完成耗时:{FullTime}s 执行次数 {TestTimes_}次 单次平均耗时:{round(FullTime/TestTimes_,4)}s 总共失败次数(含重试次数) {AllFailsNum}次')
                return ret
            return func_inner
        return func_out
if __name__ == '__main__':pass
    # print(run())