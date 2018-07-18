import asyncio
import sys
import time
from queue import Queue

from config import THREADNUM, parserList, UPDATE_TIME, MINNUM, MAX_CHECK_CONCURRENT_PER_PROCESS, MAX_DOWNLOAD_CONCURRENT
from db.DataStore import store_data, sqlhelper

'''
这个类的作用是描述爬虫的逻辑
'''

def startProxyCrawl(queue, db_proxy_num,myip):
    crawl = ProxyCrawl(queue, db_proxy_num,myip)
    crawl.run()

class ProxyCrawl:
    proxies = set()

    def __init__(self, queue, db_proxy_num,myip):
        self.queue = queue
        self.db_proxy_num = db_proxy_num
        self.myip = myip

    async def run(self):
        while True:
            self.proxies.clear()
            str = 'IPProxyPool----->>>>>>>>beginning'
            sys.stdout.write(str + "\r\n")
            sys.stdout.flush()
            proxylist = sqlhelper.select()

            tasks = []
            for proxy in proxylist:
                tasks.append()







if __name__ == '__main__':

    pass














