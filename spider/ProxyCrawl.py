import asyncio
import sys
from asyncio import Queue

from config import THREADNUM, parserList, UPDATE_TIME, MINNUM, MAX_DOWNLOAD_CONCURRENT
from db.DataStore import store_data, sqlhelper
from spider.HtmlDownloader import Html_Downloader
from spider.HtmlPraser import Html_Parser
from validator.Validator import check_proxy_effectivity
from util.tqdm import *


async def startProxyCrawl(queue, db_proxy_num, myip):
    crawl = ProxyCrawl(queue, db_proxy_num, myip)
    asyncio.ensure_future(crawl.run())


class ProxyCrawl:
    proxies = set() #作用：1.计数，2.去重

    def __init__(self, queue, db_proxy_num, myip, executor=None):
        self.queue = queue
        self.db_proxy_num = db_proxy_num
        self.myip = myip
        self.executor = executor

    async def run(self):
        loop = asyncio.get_event_loop()
        while True:
            self.proxies.clear()
            str = 'IPProxyPool----->>>>>>>>beginning'
            sys.stdout.write(str + "\r\n")
            sys.stdout.flush()
            proxylist = await loop.run_in_executor(self.executor, sqlhelper.select)  # 从数据库取出所有数据
            if proxylist:
                future_list = [asyncio.ensure_future(check_proxy_effectivity(self.myip, proxy, self.proxies)) for proxy in proxylist]
                for future in tqdm(asyncio.as_completed(future_list),total=len(future_list)):   # 在线检测所有ip有效性
                    await future
            proxy_total = len(self.proxies)
            self.db_proxy_num["value"] = proxy_total
            str = 'IPProxyPool----->>>>>>>>db exists ip:%d' % proxy_total

            crawl_task_list = []
            if proxy_total < MINNUM:    #TODO 仅仅只是统计总数的话，可能高匿的proxy已经没了，还没开始爬
                str += '\r\nIPProxyPool----->>>>>>>>now ip num < MINNUM,start crawling...'
                sys.stdout.write(str + "\r\n")
                sys.stdout.flush()
                # 开始爬取
                for parser in parserList:
                    # 针对parserList中的每一条单独设置并发数
                    semphore = asyncio.Semaphore(value=MAX_DOWNLOAD_CONCURRENT)
                    task = asyncio.ensure_future(self.crawl(parser, semphore))
                    crawl_task_list.append(task)
            else:
                str += '\r\nIPProxyPool----->>>>>>>>now ip num meet the requirement,wait UPDATE_TIME...'
                sys.stdout.write(str + "\r\n")
                sys.stdout.flush()

            await asyncio.sleep(UPDATE_TIME)
            if crawl_task_list:     #如果有爬取任务，等任务全部完成后再进入下一轮
                await asyncio.wait(crawl_task_list)

    async def crawl(self, parser, semphore):
        html_parser = Html_Parser()
        todo_list = [Html_Downloader.download(url, semphore) for url in parser['urls']]
        for future in asyncio.as_completed(todo_list):
            response = await future
            if not response:
                continue
            proxylist = html_parser.parse(response, parser)
            if not proxylist:
                continue
            for proxy in proxylist:
                proxy_str = '%s:%s' % (proxy['ip'], proxy['port'])
                if proxy_str not in self.proxies:
                    self.proxies.add(proxy_str)
                    await self.queue.put(proxy)


if __name__ == '__main__':
    pass
