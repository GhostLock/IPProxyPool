import asyncio
import aiohttp

from test.getProxy import get_proxies

test_url = 'http://www.baidu.com'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
}

async def main():
    proxy_list = await get_proxies(types=0, count=5, country='国内', protocol=0)
    print(proxy_list)


async def get_proxy():
    #TODO 从proxy_list中随机获取一个proxy，使用失败时标记打分，分数达到上限时删除此proxy
    #TODO 问题：如果维护一个proxy池，那和ipproxypool干的有什么区别？应该在使用proxy时检测，检测完立马就用。(一次检测一次使用)
    #TODO 确保同一个ip在爬虫全局的sleeptime内不会再次被唤醒
    pass

async def case01():
    proxy = await get_proxy()
    async with aiohttp.ClientSession() as session:
        async with session.get(test_url,headers=headers,proxy=proxy) as response:
            # response = aiohttp.ClientResponse()
            status = response.status
            print(status)

def ordered_choice():
    #代表爬虫中全局的sleeptime
    sleep_time = 2
    """
    代表n个获取的proxy，
    要求：
    1.确保同一个proxy在sleep_time内不会被使用
    2.全部proxy都在sleep_time内时阻塞协程（交出loop控制权）
    3.对proxy计分，分满就调用删除接口
    4.
    """
    list_orgin = ['proxy-{}'.format(n) for n in range(1,6)]


if __name__ == '__main__':
    ordered_choice()
    exit()


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()