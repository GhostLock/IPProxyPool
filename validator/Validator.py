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


def detect_from_db(myip, proxy, proxies_set):
    proxy_dict = {'ip': proxy[0], 'port': proxy[1]}
    result = detect_proxy(myip, proxy_dict)
    if result:
        proxy_str = '%s:%s' % (proxy[0], proxy[1])
        proxies_set.add(proxy_str)

    else:
        if proxy[2] < 1:
            sqlhelper.delete({'ip': proxy[0], 'port': proxy[1]})
        else:
            score = proxy[2] - 1
            sqlhelper.update({'ip': proxy[0], 'port': proxy[1]}, {'score': score})
            proxy_str = '%s:%s' % (proxy[0], proxy[1])
            proxies_set.add(proxy_str)


def detect_proxy(selfip, proxy, queue2=None):
    '''
    :param proxy: ip字典
    :return:
    '''
    ip = proxy['ip']
    port = proxy['port']
    proxies = {"http": "http://%s:%s" % (ip, port), "https": "http://%s:%s" % (ip, port)}
    protocol, types, speed = getattr(sys.modules[__name__], config.CHECK_PROXY['function'])(selfip,proxies)  # checkProxy(selfip, proxies)
    if protocol >= 0:   #如果是有效的ip
        proxy['protocol'] = protocol
        proxy['types'] = types
        proxy['speed'] = speed
    else:
        proxy = None
    if queue2:
        queue2.put(proxy)
    return proxy


def checkProxy(selfip, proxies):
    '''
    用来检测代理的类型，突然发现，免费网站写的信息不靠谱，还是要自己检测代理的类型
    '''
    protocol = -1
    types = -1
    speed = -1
    http, http_types, http_speed = _checkHttpProxy(selfip, proxies)
    https, https_types, https_speed = _checkHttpProxy(selfip, proxies, False)
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
                    print(content)
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

    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(_checkHttpProxy(selfip, proxies))
    loop.close()

    print(res)

    pass