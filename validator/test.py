import asyncio
import aiohttp

loop = asyncio.get_event_loop()

async def test():
    async with aiohttp.ClientSession() as session:
        async with session.get(url='http://www.baidu.com/') as response:
            print(response.status)
            print(response.reason)

def test01():
    print(loop)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
    loop.close()
