import sys
import asyncio
import aiohttp

import chardet
# from gevent import monkey
# monkey.patch_all()

import json
import os
# import gevent
# import requests
import time
# import psutil
# from multiprocessing import Process, Queue

import config
from db.DataStore import sqlhelper
from util.exception import Test_URL_Fail

loop = asyncio.get_event_loop()

async def detect_from_db(myip, proxy, proxies_set,executor=None):
    """
    从数据库读取ip dict ,并在线检测。
    :param myip:
    :param proxy:
    :param proxies_set:
    :return:
    """

    proxy_dict = {'ip': proxy[0], 'port': proxy[1]}
    result = await detect_proxy(myip, proxy_dict)
    if result:
        proxy_str = '%s:%s' % (proxy[0], proxy[1])
        proxies_set.add(proxy_str)

    else:
        if proxy[2] < 1:    #如果分数扣光了，就删掉
            await loop.run_in_executor(executor,sqlhelper.delete,{'ip': proxy[0], 'port': proxy[1]})
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
    proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}
    protocol, types, speed = await getattr(sys.modules[__name__], config.CHECK_PROXY['function'])(selfip,proxies)  # checkProxy(selfip, proxies)
    if protocol >= 0:   #如果是有效的ip
        proxy['protocol'] = protocol    #http/https的协议类型 #TODO 这个参数是否有用，有待考证！！
        proxy['types'] = types
        proxy['speed'] = speed
    else:
        proxy = None
    if queue2:
        queue2.put(proxy) #TODO 这里会造成queue2里有None值。
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
    :param isHttp:  是否是https
    :return:    是否可用，类型，速度
    """
    types = -1
    speed = -1
    if isHttp:
        test_url = config.TEST_HTTP_HEADER
        proxy = proxies.get('http')
    else:
        test_url = config.TEST_HTTPS_HEADER
        proxy = proxies.get('https')
    try:
        timeout = aiohttp.ClientTimeout(total=config.TIMEOUT)
        start = time.time()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url=test_url,headers=config.get_header(),proxy=proxy) as response:
                if response.reason == "OK":
                    speed = round(time.time() - start, 2)   #时间四舍五入保留小数点后2位
                    content = await response.json()
                    headers = content['headers']
                    ip = content['origin']
                    proxy_connection = headers.get('Proxy-Connection', None)
                    #TODO 检测方式是否有效，有待考证！！
                    if ip == selfip:
                        return False, types, speed
                    if ',' in ip:
                        types = 2   #透明
                    elif proxy_connection:
                        types = 1   #匿名
                    else:
                        types = 0   #高匿
                    return True, types, speed
                else:
                    return False, types, speed
    except Exception as e:
        return False, types, speed


if __name__ == '__main__':
    selfip = "121.0.29.197"
    ip = '101.96.11.5'
    port = 80
    proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}
    from queue import Queue
    q = Queue()
    loop = asyncio.get_event_loop()
    proxy = ('121.0.29.197', 80, 10)
    proxy_dict = {'ip': proxy[0], 'port': proxy[1]}
    res = loop.run_until_complete(detect_proxy(selfip, proxy_dict,q))
    loop.close()
    print(res,q.get(timeout=2))

    pass