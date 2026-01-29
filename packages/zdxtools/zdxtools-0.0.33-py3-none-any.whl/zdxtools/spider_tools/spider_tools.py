#爬虫相关
import os
import time

class spider_tools:
    headerstr = {
        'Chrome': '''
                    Connection: keep-alive
                    sec-ch-ua: " Not;A Brand";v="99", "Microsoft Edge";v="97", "Chromium";v="97"
                    Accept: */*
                    sec-ch-ua-mobile: ?0
                    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62
                    sec-ch-ua-platform: "Windows"
                    Sec-Fetch-Site: same-site
                    Sec-Fetch-Mode: cors
                    Sec-Fetch-Dest: empty
                    Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6
                '''
    }
    #格式化请求头
    @classmethod
    def return_header(cls,str1 = '',choice = None):
        '''
        输入请求头原字符串，返回格式化的字典用于request请求
        :param choice: 可以直接指定简单的浏览器头 目前可以选择 Chrome
        spider_tools.return_header(choice='Chrome')
        :param str1:
            Host: api.bilibili.com
            Connection: keep-alive
            Content-Length: 69
            sec-ch-ua: " Not;A Brand";v="99", "Microsoft Edge";v="97", "Chromium";v="97"
            Accept: */*
            sec-ch-ua-mobile: ?0
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62
            sec-ch-ua-platform: "Windows"
            Origin: https://www.bilibili.com
            Sec-Fetch-Site: same-site
            Sec-Fetch-Mode: cors
            Sec-Fetch-Dest: empty
            Referer: https://www.bilibili.com/
            Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6
        :return:
        '''
        if choice:
            return cls.return_header(str1 = cls.headerstr['Chrome'])
        headers = {}
        for i in str1.split('\n'):
            if len(i) == 0:continue
            ret = i.split(':',1)
            if len(ret) == 1:continue
            headers[ret[0].strip()] = ret[1].strip()
        return headers
    #格式化params 字符串为字典
    @classmethod
    def return_params(cls,paramstr):
        '''
        :param paramstr:
        lq=0&pq=%5Ct&sc=10-2&qs=n&sk=&cvid=CA0FE963090A44C5B8E4C0F762F3C395&ghsh=0&ghacc=0&ghpl=
        :return:
        '''
        paramsdic = {}
        for i in paramstr.split('&'):
            ret = i.split('=')
            paramsdic[ret[0]] = ret[1]
        return paramsdic

    @classmethod
    def turn_fiddler_payload(cls,raw,splitStr = '\t'):
        '''
        :param raw:
            fidder的payload字符串
            rid	614813283
            type	2
            add_media_ids	803369703
            del_media_ids
            platform	web
            eab_x	2
            ramval	1
            ga	1
            gaia_source	web_normal
            csrf
        :return: 返回字典
        '''
        try:
            newdata = [i.strip() for i in raw.split('\n') if len(i.strip()) > 0]
            payload ={}
            for f in newdata:
                fgdata = f.split(splitStr)
                if len(fgdata) > 1:
                    payload[fgdata[0]] = fgdata[1]
                else:
                    payload[fgdata[0]] = ''
            return  payload
        except:
            print('1')
            return cls.turn_fiddler_payload_error(raw)

    # 格式化fiddler的请求头
    @classmethod
    def turn_fiddler_payload_error(cls,raw):
        '''
        遗弃，有问题，为了更好的体验请使用 方法turn_fiddler_payload
        :param raw:
        :return:
        '''
        newdata = [ i.replace('        ','') for i in raw.split('\n') if len(i.replace('        ','')) >0]
        payload ={}
        for f in newdata:
            fgdata = f.split('\t')
            payload[fgdata[0]] = fgdata[1]
        return  payload
    # 下载的标题特俗符号处理
    @classmethod
    def title_replace(cls,title):
        '''
        :param title: 传入要更改的名字
        :return:
        '''
        title = title.replace('/', ' ').replace('?', '').replace('!', '').replace(',', '').replace('*', '').replace(':','').replace('★', '').replace('|', '').replace('\\', " ")
        return title
    #根据Url地址图片文件名获得文件名
    @classmethod
    def GetUrlPicFileName(cls,url):
        '''

        :param url:193e945f30aa9985e69f9893d01a2bdc_720w.png?a=1  类似这样的形式
        :return:
        '''

        return  os.path.basename(url[0]).split('.')[-1].split('?')[0]
    #返回文件下载的标题
    @classmethod
    def get_downfilename(cls,ret):
        '''

        :param ret: 传入响应体
        :return:
        '''
        name = spider_tools.title_replace(ret.headers.get('Content-Disposition').encode('ISO-8859-1').decode('utf8').split('filename=')[1])
        return name

    #下载图片
    @classmethod
    def down_pic(cls,path,url,header = None,FailTime = 0,FailSleepTime = 1,proxies = False):
        import requests
        '''
        :param path: 传入存放地址
        :param url: 下载链接
        :param header: 请求头，最好包含cookie
        :param FailTime  失败次数  尝试三次 返回False
        :param FailSleepTime 失败间隔时间 默认为1 秒
        :return: 下载成功返回true ，下载失败返回false
        '''
        if not header:
            header = cls.return_header(choice=True)
        FailTimeALL = 0
        while True:
            try :
                data = requests.get(url,headers= header,verify=False,stream=True,proxies = proxies).content
                with open(path,mode='wb') as f :
                    f.write(data)
                return True
            except:
                if FailTimeALL >= FailTime:
                    return False
                time.sleep(FailSleepTime)
                FailTimeALL += 1
        # try :
        #     r = requests.get(url,headers= header,verify=False, stream=True)
        #     f = open(path, "wb")
        #     for chunk in r.iter_content(chunk_size=512):
        #         if chunk:
        #             f.write(chunk)
        #         return True
        # except:
        #     return  False
    #智能网址拼接
    @classmethod
    def smart_url_join(cls,base_url, *paths, ensure_trailing_slash=False):
        """
        智能URL拼接函数

        Args:
            base_url: 基础URL
            *paths: 多个路径部分
            ensure_trailing_slash: 是否确保base_url以/结尾
        """
        from urllib.parse import urljoin, urlparse

        if ensure_trailing_slash and not base_url.endswith('/'):
            # 解析URL，确保路径部分以/结尾
            parsed = urlparse(base_url)
            if not parsed.path.endswith('/'):
                base_url = base_url.rstrip('/') + '/'

        result = base_url
        for path in paths:
            result = urljoin(result.rstrip('/') + '/', path.lstrip('/'))

        return result

    #处理路径的特殊字符
    @classmethod
    def path_clean(self,path):
        return path.strip('\u202a')
    #返回绕过检测的selenium浏览器driver
    @classmethod
    def GetDriver(cls,chrome_options = False,**kwargs):
        '''
        :param chrome_options: 传入
        :return:
        '''
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver import Chrome
        if chrome_options:
            chrome_options = chrome_options
        else:
            chrome_options = Options()
        chrome_options.add_argument("disable-blink-features=AutomationControlled")
        driver = Chrome( options=chrome_options,**kwargs)
        stealthJsPath = os.path.join(os.path.dirname(__file__),'source','stealth.min.js')
        with open(stealthJsPath) as f:
            js = f.read()
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": js
        })
        return  driver