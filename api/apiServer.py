import asyncio
import sys
import base64
import time
from aiohttp import web
from concurrent.futures import ThreadPoolExecutor
from aiohttp_session import setup,get_session,SimpleCookieStorage
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

import config
from db.DataStore import sqlhelper
from validator.Validator import check_proxy_effectivity_server, getMyIP


def start_api_server():
    app = init_app()
    web.run_app(app, host=config.HOST, port=config.PORT)


def init_app():
    app = web.Application()
    setup_routes(app)
    # 对windows系统的支持
    windows_support(app)
    # 设置额外的executor
    app.on_startup.append(init_executor)  # signal 是协程
    app.on_startup.append(get_myip)
    app.on_cleanup.append(clean_executor)
    #启用session(使用EncryptedCookieStorage)
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))
    # setup(app,SimpleCookieStorage())    #TODO used only in test!
    return app


def windows_support(app):
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)


async def init_executor(app):
    executor = ThreadPoolExecutor(max_workers=config.SERVER_EXECUTOR_NUM)
    app['executor'] = executor


async def clean_executor(app):
    app['executor'].shutdown(wait=True)


async def get_myip(app):
    app['myip'] = await getMyIP()


def setup_routes(app):
    app.add_routes([
        web.get('/', select),
        web.get('/delete', delete),
        web.get('/safemode', safemode),
        web.get('/set_cookie',set_cookie),
        web.get('/get_cookie',get_cookie),
    ])


async def select(request):
    params = request.query
    app = request.app
    loop = app.loop
    data = await loop.run_in_executor(app['executor'], sqlhelper.select, params.get('count', None), params)
    return web.json_response(data=data)


async def delete(request):
    params = request.query
    app = request.app
    loop = app.loop
    data = await loop.run_in_executor(app['executor'], sqlhelper.delete, params)
    return web.json_response(data=data)


async def safemode(request):    #   TODO 有的时候会报错：OSError: [WinError 87] 参数错误。
    session = await get_session(request)    #TODO aiohttp_session把session值都存cookie里，而cookie值有大小限制！！
    params = dict(request.query)
    sleep = int(params.pop('sleep')) if 'sleep' in params else 0
    app = request.app
    loop = app.loop
    myip = app['myip']
    if not session.get('exclude_ip'):
        session['exclude_ip'] = {}
    exclude_ip = {ip:starttime for ip,starttime in session['exclude_ip'].items() if round(time.time()-starttime) < sleep}
    # for ip, starttime in session['exclude_ip'].items():
    #     bre = round(time.time()-starttime)
    #     print(bre)
    #     print(bre >= sleep)
    # print('before------')
    # print(exclude_ip)
    data_list = await loop.run_in_executor(app['executor'], sqlhelper.select, params.get('count', None), params,exclude_ip)
    # data: ('101.96.11.5', 80, 10, 0, 0)
    future_list = [check_proxy_effectivity_server(myip, data, app['executor']) for data in data_list]
    proxy_list = []
    for future in asyncio.as_completed(future_list):
        proxy = await future
        if proxy:  # {'ip': '101.96.11.5', 'port': 80, 'protocol': 0, 'types': 0, 'speed': 0.26}
            exclude_ip[proxy['ip']] = time.time()
            proxy_list.append(proxy)
    session['exclude_ip'] = exclude_ip  #if not do this,session won't set
    # print('after------')
    # print(session['exclude_ip'])
    # print('----------------------------------------------------------------------')
    return web.json_response(data=proxy_list)


async def set_cookie(request):
    session = await get_session(request)
    session['test'] = 123
    session['test02'] = "234"
    return web.json_response(data={})

async def get_cookie(request):
    session = await get_session(request)
    if not session.get('proxy_list'):
        session['proxy_list'] = [1,2,3]
    proxy_list = session['proxy_list']
    print(proxy_list)

    return web.json_response(data=dict(session))


if __name__ == '__main__':
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor() as process:
        process.submit(start_api_server)
