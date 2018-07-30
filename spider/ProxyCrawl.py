import asyncio
import sys
from asyncio import Queue

from config import THREADNUM, parserList, UPDATE_TIME, MINNUM, MAX_CHECK_CONCURRENT_PER_PROCESS, MAX_DOWNLOAD_CONCURRENT
from db.DataStore import store_data, sqlhelper
from spider.HtmlDownloader import Html_Downloader
from spider.HtmlPraser import Html_Parser
from validator.Validator import check_proxy_effectivity

'''
这个类的作用是描述爬虫的逻辑
'''
loop = asyncio.get_event_loop()


async def startProxyCrawl(queue, db_proxy_num, myip):
    crawl = ProxyCrawl(queue, db_proxy_num, myip)
    asyncio.ensure_future(crawl.run())


class ProxyCrawl:
    proxies = set()

    def __init__(self, queue, db_proxy_num, myip, executor=None):
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
            proxylist = await loop.run_in_executor(self.executor, sqlhelper.select)  # 从数据库取出所有数据
            if proxylist:
                future_list = [asyncio.ensure_future(check_proxy_effectivity(self.myip, proxy, self.proxies)) for proxy in proxylist]
                await asyncio.wait(future_list)  # 在线检测所有ip有效性
            proxy_total = len(self.proxies)
            self.db_proxy_num["value"] = proxy_total
            str = 'IPProxyPool----->>>>>>>>db exists ip:%d' % proxy_total

            if proxy_total < MINNUM:
                str += '\r\nIPProxyPool----->>>>>>>>now ip num < MINNUM,start crawling...'
                sys.stdout.write(str + "\r\n")
                sys.stdout.flush()
                # 开始爬取
                for p in parserList:
                    asyncio.ensure_future(self.crawl(p))
            else:
                str += '\r\nIPProxyPool----->>>>>>>>now ip num meet the requirement,wait UPDATE_TIME...'
                sys.stdout.write(str + "\r\n")
                sys.stdout.flush()

            await asyncio.sleep(UPDATE_TIME)

    async def crawl(self, parser):
        html_parser = Html_Parser()
        for url in parser['urls']:
            response = await Html_Downloader.download(url)  #todo 这里没有并发，是否需要改？
            if response is not None:
                proxylist = html_parser.parse(response, parser)
                if proxylist is not None:
                    for proxy in proxylist:
                        proxy_str = '%s:%s' % (proxy['ip'], proxy['port'])
                        if proxy_str not in self.proxies:
                            self.proxies.add(proxy_str)
                            while True:
                                if self.queue.full():  # TODO 这个队列是否需要
                                    await asyncio.sleep(0.1)
                                else:
                                    await self.queue.put(proxy)
                                    # print(proxy)    #todo testing...
                                    break


if __name__ == '__main__':

    pass
