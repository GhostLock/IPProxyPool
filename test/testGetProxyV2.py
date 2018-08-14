import aiohttp
import asyncio
import re

test_url = "http://httpbin.org/get"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
}
ipproxypool_url = 'http://127.0.0.1:8000'


async def get_proxies(**kwargs):
    """
    获取一组代理，并验证有效性。返回空列表时raise Exception
    :param kwargs:
        types(int),0: 高匿,1:匿名,2: 透明
        protocol(int),0: http, 1: https, 2: http/https
        count(int),数量
        country(str), 取值为 国内, 国外
        area(int),地区
    :return: list of proxy url
    """
    url = ipproxypool_url + '/?' + '&'.join([str(k) + '=' + str(v) for k, v in kwargs.items()])
    semaphore = asyncio.Semaphore(value=20)
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            proxy_list = await response.json()
    # 在输出之前验证一下
    tasks = [asyncio.ensure_future(_get_http_info(proxy, semaphore, timeout)) for proxy in proxy_list]
    proxy_list = []
    for future in asyncio.as_completed(tasks):
        try:
            res = await future
            json_response = res[0]
            proxy = res[1]
            if kwargs.get('types') == 0:
                origin = json_response.get("origin")
                if ',' in origin:  # 非高匿名，例如：121.0.29.203, 212.129.17.35
                    continue
            proxy_list.append('http://{ip}:{port}'.format(ip=proxy[0], port=proxy[1]))
        except Exception:
            pass
    if not proxy_list:
        raise Exception("Got no proxy !")
    return proxy_list


async def delete_proxy(proxy_url):
    """
    从数据库删除代理。无法解析proxy_url时raise Exception
    :param proxy_url:  http://ip:port
    """
    pattern = 'http://(.*?):(\d+)'
    res = re.match(pattern, proxy_url)
    if not res:
        raise Exception('Unusual proxy_url:{} !'.format(proxy_url))
    ip, port = res.group(1), res.group(2)
    url = ipproxypool_url + "/delete?ip={ip}&port={port}".format(ip=ip, port=port)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            pass


async def _get_http_info(proxy, semaphore, timeout):
    ip = proxy[0]
    port = proxy[1]
    proxy_url = "http://{ip}:{port}".format(ip=ip, port=port)
    async with semaphore:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(test_url, proxy=proxy_url, headers=headers) as response:
                json_response = await response.json()
                return json_response, proxy


if __name__ == '__main__':
    url = 'http://127.0.0.1:8000/?types=0&count=5&country=国内&protocol=0'
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(get_proxies(types=0, count=5, country='国内', protocol=0))
    # res = loop.run_until_complete( delete_proxy('190.147.43.62','53281'))
    loop.close()
    print(res)
