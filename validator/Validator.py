import sys
import asyncio
import aiohttp
import time

from asyncio import Semaphore
from asyncio import Queue

import config
from db.DataStore import sqlhelper
from util.exception import Test_URL_Fail


semphore = asyncio.Semaphore(value=config.MAX_CHECK_CONCURRENT)

async def validator(queue1, queue2, myip):
    """
    从queue1中取出proxy，进行验证后存入queue2
    :param queue1: 存放下载的proxy
    :param queue2: 存放经过验证的proxy
    :param myip: 本机的ip
    """
    while True:
        proxy = await queue1.get()
        asyncio.ensure_future(detect_proxy(myip, proxy, queue2))



async def check_proxy_effectivity(myip, proxy, proxies_set, executor=None):
    """
    从数据库读取ip dict ,并在线检测。
    :param myip:
    :param proxy:
    :param proxies_set:
    :return:
    """
    loop = asyncio.get_event_loop()
    proxy_dict = {'ip': proxy[0], 'port': proxy[1]}
    result = await detect_proxy(myip, proxy_dict)
    if result:
        proxy_str = '%s:%s' % (proxy[0], proxy[1])
        proxies_set.add(proxy_str)
    else:
        #采用计分制，每检测一次不通过就扣一分
        if proxy[2] < 1:  # 如果分数扣光就删掉
            await loop.run_in_executor(executor, sqlhelper.delete, {'ip': proxy[0], 'port': proxy[1]})
        else:
            score = proxy[2] - 1
            await loop.run_in_executor(executor, sqlhelper.update, {'ip': proxy[0], 'port': proxy[1]}, {'score': score})
            proxy_str = '%s:%s' % (proxy[0], proxy[1])
            proxies_set.add(proxy_str)


async def detect_proxy(selfip, proxy, queue2=None):
    '''
    读取配置文件中的检测函数方法名，并调用。
    :param proxy: ip字典
    :return:
    '''
    ip = proxy['ip']
    port = proxy['port']
    proxies = "http://%s:%s" % (ip, port)   #只有http proxy，哪怕支持https类型的proxy也写成http, https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/CONNECT
    protocol, types, speed = await getattr(sys.modules[__name__], config.CHECK_PROXY['function'])(selfip,proxies)  # checkProxy(selfip, proxies)
    if protocol >= 0:  # 如果是有效的ip
        proxy['protocol'] = protocol  # http/https的协议类型 #TODO 这个参数是否有用，有待考证！！
        proxy['types'] = types
        proxy['speed'] = speed
    else:
        proxy = None
    if queue2:
        await queue2.put(proxy) #None值会被用于标记Fail ip数
        # print(proxy)
    return proxy


async def checkProxy(selfip, proxies):
    '''
    用来检测代理的类型，突然发现，免费网站写的信息不靠谱，还是要自己检测代理的类型
    '''
    protocol = -1
    types = -1
    speed = -1
    http, http_types, http_speed = await _checkHttpProxy(selfip, proxies)
    https, https_types, https_speed = await _checkHttpProxy(selfip, proxies, False)
    if http and https:
        protocol = 2
        types = http_types
        speed = http_speed
    elif http:
        types = http_types
        protocol = 0
        speed = http_speed
    elif https:
        types = https_types
        protocol = 1
        speed = https_speed
    else:
        types = -1
        protocol = -1
        speed = -1
    return protocol, types, speed


async def _checkHttpProxy(selfip, proxies, isHttp=True):
    """
    检测当前ip
    :param selfip:  本机IP
    :param proxies: 代理ip
    :param isHttp:  是否是http
    :return:    是否可用，类型，速度
    """
    types = -1
    speed = -1
    if isHttp:
        test_url = config.TEST_HTTP_HEADER
    else:
        test_url = config.TEST_HTTPS_HEADER
    async with semphore:
        try:
            timeout = aiohttp.ClientTimeout(total=config.TIMEOUT)
            start = time.time()
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url=test_url, headers=config.get_header(), proxy=proxies) as response:
                    if response.reason == "OK":
                        speed = round(time.time() - start, 2)  # 时间四舍五入保留小数点后2位
                        content = await response.json()
                        headers = content['headers']
                        ip = content['origin']
                        proxy_connection = headers.get('Proxy-Connection', None)
                        # TODO 检测方式是否有效，有待考证！！
                        if ip == selfip:
                            return False, types, speed
                        if ',' in ip:
                            types = 2  # 透明
                        elif proxy_connection:
                            types = 1  # 匿名
                        else:
                            types = 0  # 高匿
                        return True, types, speed
                    else:
                        return False, types, speed
        except Exception as e:
            return False, types, speed


async def getMyIP():
    try:
        timeout = aiohttp.ClientTimeout(total=config.TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url=config.TEST_IP, headers=config.get_header()) as response:
                ip = await response.json()
                return ip['origin']
    except Exception as e:
        raise Test_URL_Fail


if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # res = loop.run_until_complete(getMyIP())
    # loop.close()
    # print(res)

    pass
