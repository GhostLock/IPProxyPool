import aiohttp
import asyncio

proxypool_url = 'http://localhost:8000/'  # 不能使用http://127.0.0.1:8000/否则无法获取cookie

__semphore = asyncio.Semaphore(value=1)


def __safecheck(coroutine):
    async def check(session=None, safemode=True, **kwargs):
        if safemode and not session:
            raise Exception('safemode require session to work!')
        elif not safemode:
            async with aiohttp.ClientSession() as session:
                result = await coroutine(session, safemode, **kwargs)
        else:
            result = await coroutine(session, safemode, **kwargs)
        return result
    return check


@__safecheck
async def get_proxy(session=None, safemode=True, **kwargs):
    """
    获取ip代理
    :param kwargs:
        types(int),0: 高匿,1:匿名,2: 透明
        protocol(int),0: http, 1: https, 2: http/https
        count(int),数量
        country(str), 取值为 国内, 国外
        area(int),地区
        sleep(int):proxy冷却时间（秒）
    :param safemode:使用安全模式,返回proxy时进行验证，并不返回在sleep时间内的proxy
    :return: list of proxy url / raise Exception
    """
    url = proxypool_url + ('safemode?' if safemode else '?')
    url += '&'.join(['{}={}'.format(k, v) for k, v in kwargs.items()])
    async with __semphore:  # TODO(有待改善) 这里制造了一个单并发的瓶颈，防止并发使服务端返回相同的proxy
        async with session.get(url) as response:
            proxy_list = await response.json()
    proxy_urls = ['http://{}:{}'.format(proxy['ip'], proxy['port']) for proxy in proxy_list]
    return proxy_urls


if __name__ == '__main__':
    async def case02():
        timeout = aiohttp.ClientTimeout(total=30)
        session = aiohttp.ClientSession(timeout=timeout)
        params = {
            'session': session,
            'count': 3,
            'types': 0,
            'protocol': 0,
            'country': '国内',
            'sleep': 30
        }
        res = asyncio.gather(get_proxy(**params), get_proxy(**params), get_proxy(**params))
        print(await res)
        await session.close()


    async def main():
        await case02()


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
