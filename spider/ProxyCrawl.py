import asyncio
import sys
import time
from queue import Queue

from config import THREADNUM, parserList, UPDATE_TIME, MINNUM, MAX_CHECK_CONCURRENT_PER_PROCESS, MAX_DOWNLOAD_CONCURRENT
from db.DataStore import store_data, sqlhelper
from spider.HtmlDownloader import Html_Downloader
from spider.HtmlPraser import Html_Parser
from validator.Validator import detect_from_db
'''
这个类的作用是描述爬虫的逻辑
'''
loop = asyncio.get_event_loop()

def startProxyCrawl(queue, db_proxy_num,myip):
    crawl = ProxyCrawl(queue, db_proxy_num,myip)
    crawl.run()

class ProxyCrawl:
    proxies = set()

    def __init__(self, queue, db_proxy_num,myip,executor=None):
        self.queue = queue
        self.db_proxy_num = db_proxy_num
        self.myip = myip
        self.executor = executor

    async def run(self):
        while True:
            self.proxies.clear()
            str = 'IPProxyPool----->>>>>>>>beginning'
            sys.stdout.write(str + "\r\n")
            sys.stdout.flush()
            proxylist = await loop.run_in_executor(self.executor,sqlhelper.select)  #从数据库取出所有数据

            future_list = [asyncio.ensure_future(detect_from_db(self.myip, proxy, self.proxies)) for proxy in proxylist]
            await asyncio.wait(future_list)     #在线检测所有ip有效性
            proxy_total = len(self.proxies)
            self.db_proxy_num.value = proxy_total
            str = 'IPProxyPool----->>>>>>>>db exists ip:%d' % proxy_total

            if proxy_total < MINNUM:
                str += '\r\nIPProxyPool----->>>>>>>>now ip num < MINNUM,start crawling...'
                sys.stdout.write(str + "\r\n")
                sys.stdout.flush()
                #开始爬取
                for p in parserList:
                    pass






    def crawl(self, parser):
        html_parser = Html_Parser()
        for url in parser['urls']:
            response = Html_Downloader.download(url)
            # if response is not None:
            #     proxylist = html_parser.parse(response, parser)
            #     if proxylist is not None:
            #         for proxy in proxylist:
            #             proxy_str = '%s:%s' % (proxy['ip'], proxy['port'])
            #             if proxy_str not in self.proxies:
            #                 self.proxies.add(proxy_str)
            #                 while True:
            #                     if self.queue.full():
            #                         time.sleep(0.1)
            #                     else:
            #                         self.queue.put(proxy)
            #                         break





if __name__ == '__main__':
    print(parserList[0])
    """
    {'urls': ['http://www.66ip.cn/index.html', 'http://www.66ip.cn/2.html', 'http://www.66ip.cn/3.html', 'http://www.66ip.cn/4.html', 'http://www.66ip.cn/5.html', 'http://www.66ip.cn/6.html', 'http://www.66ip.cn/7.html', 'http://www.66ip.cn/8.html', 'http://www.66ip.cn/9.html', 'http://www.66ip.cn/10.html', 'http://www.66ip.cn/11.html'], 'type': 'xpath', 'pattern': ".//*[@id='main']/div/div[1]/table/tr[position()>1]", 'position': {'ip': './td[1]', 'port': './td[2]', 'type': './td[4]', 'protocol': ''}}
    """
    pass














