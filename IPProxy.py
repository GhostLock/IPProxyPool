import asyncio
import sys
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from api.apiServer import start_api_server
from db.DataStore import store_data
from validator.Validator import validator, getMyIP
from spider.ProxyCrawl import startProxyCrawl

from config import TASK_QUEUE_SIZE


async def spider_main():
    myip = await getMyIP()
    DB_PROXY_NUM = {"value": 0}
    q1 = Queue(maxsize=TASK_QUEUE_SIZE)  # 存放下载的proxy
    q2 = Queue()  # 存放经过验证的proxy
    asyncio.ensure_future(startProxyCrawl(q1, DB_PROXY_NUM, myip))
    asyncio.ensure_future(validator(q1, q2, myip))
    asyncio.ensure_future(store_data(q2, DB_PROXY_NUM))


def spider_process():
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()

    # 暂不使用，因为asyncio.ProactorEventLoop() 不支持proxy代理类型为https
    # if sys.platform == 'win32':  # 在windows平台上使用socket连接，默认限制连接数为512，
    #     loop = asyncio.ProactorEventLoop()
    #     asyncio.set_event_loop(loop)

    loop.set_default_executor(executor)
    asyncio.ensure_future(spider_main())
    loop.run_forever()


if __name__ == "__main__":
    with ProcessPoolExecutor() as executor:
        try:
            executor.submit(spider_process)
            executor.submit(start_api_server)
        except KeyboardInterrupt:
            pass
