import aiohttp
import asyncio
from pprint import pprint

from util.tqdm import *

test_url = "http://httpbin.org/get"
proxy_url_pre = "http://127.0.0.1:8000/?types={}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
}


async def get_proxy(type):
    async with aiohttp.ClientSession() as session:
        async with session.get(proxy_url_pre.format(type)) as response:
            data = await response.json()
            return data


async def get_http_info(proxy, semaphore, timeout):
    ip = proxy[0]
    port = proxy[1]
    proxy_url = "http://{ip}:{port}".format(ip=ip, port=port)
    async with semaphore:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(test_url, proxy=proxy_url, headers=headers) as response:
                data = await response.json()
                return data


async def main01(type, semaphore, timeout):
    proxy_list = await get_proxy(type)
    tasks = [asyncio.ensure_future(get_http_info(proxy, semaphore, timeout)) for proxy in proxy_list]
    result_list = []
    for future in tqdm(asyncio.as_completed(tasks),total=len(tasks)):
        try:
            res = await future
            headers = res['headers']
            del_list = ['Accept', 'Accept-Encoding', 'Connection', 'Host', 'Cache-Control']
            for head in del_list:
                if head in headers:
                    del headers[head]
            result_list.append(res)
        except Exception as e:
            pass
    return result_list

def case01():
    """
    观察所有爬过的ip再次检查时的结果
    """
    type = 0  # 0: 高匿,1:匿名,2 透明
    semaphore = asyncio.Semaphore(value=20)
    timeout = aiohttp.ClientTimeout(total=10)

    loop = asyncio.get_event_loop()
    result_list = loop.run_until_complete(main01(type, semaphore, timeout))
    loop.close()
    pprint(result_list)

def case02():
    """
    检测重复ip：（重复ip，不同端口，不是问题）
    select * from proxys where ip in (select ip from proxys group by ip having count(ip)>1)
    """


def case03():
    """
    检测高匿ip中非高匿ip(在使用代理时还要再检测)
    """
    type = 0  # 0: 高匿,1:匿名,2 透明
    semaphore = asyncio.Semaphore(value=20)
    timeout = aiohttp.ClientTimeout(total=10)

    loop = asyncio.get_event_loop()
    result_list = loop.run_until_complete(main01(type, semaphore, timeout))
    loop.close()
    pprint(result_list)
    for result in result_list:
        origin = result.get("origin")
        if  ',' in origin:
            print(origin,result)



if __name__ == '__main__':
    case03()
    """
    121.0.29.203, 212.129.17.35
    121.0.29.203, 119.188.162.164
    """


    pass
    #TODO 测试，爬完以后的ip类型，和初次储存时偏差多大？（匿名变成非匿名）,有多少重复ip
