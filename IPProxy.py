import asyncio
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor

from api.apiServer import start_api_server
from db.DataStore import store_data
from validator.Validator import validator, getMyIP
from spider.ProxyCrawl import startProxyCrawl

from config import TASK_QUEUE_SIZE


async def main():
    myip = await getMyIP()
    DB_PROXY_NUM = {"value": 0}
    q1 = Queue(maxsize=TASK_QUEUE_SIZE)     #存放下载的proxy
    q2 = Queue()    #存放经过验证的proxy
    """
    sqlalchemy 总是报错，直接使用 loop.run_in_executor() 运行sqlalchemy的orm遇到问题。
    """
    asyncio.ensure_future(startProxyCrawl(q1, DB_PROXY_NUM, myip))
    asyncio.ensure_future(validator(q1, q2, myip))
    asyncio.ensure_future(store_data(q2, DB_PROXY_NUM))


if __name__ == "__main__":
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    loop.set_default_executor(executor)
    # loop.run_in_executor(executor,start_api_server)   #TODO web服务应该使用另一个进程
    asyncio.ensure_future(main())
    loop.run_forever()
