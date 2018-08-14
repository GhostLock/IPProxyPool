import asyncio
import sys
import base64
import time
import uuid
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
    # windows_support(app)
    # 设置额外的executor
    app.on_startup.append(init_executor)  # signal 是协程
    app.on_startup.append(get_myip)
    app.on_cleanup.append(clean_executor)
    # 启用session(使用EncryptedCookieStorage)
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))
    # setup(app,SimpleCookieStorage())    # used only in test!
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
    data_list = await loop.run_in_executor(app['executor'], sqlhelper.select, params.get('count', None), params)
    result_data = [{
        'ip':data[0],
        'port':data[1],
        'protocol':data[2],
        'types':data[3],
        'speed':data[4]
    } for data in data_list]
    return web.json_response(data=result_data)


async def delete(request):
    params = request.query
    app = request.app
    loop = app.loop
    data = await loop.run_in_executor(app['executor'], sqlhelper.delete, params)
    return web.json_response(data=data)


async def safemode(request):
    """
    取出proxy，先验证有效再返回，避免proxy的类型有变化。
    添加参数"sleep"，单位秒，设置返回的proxy过多久才能再次被使用。
    注意：如果windows下使用了asyncio.ProactorEventLoop()，https验证时会报错：OSError: [WinError 87] 参数错误。
    """
    """
    aiohttp_session默认把session值都存cookie里，而cookie值有大小限制,超出整个数据都会丢失！
    可以把session值存服务端，cookie内仅仅只存sessionid
    """
    app = request.app
    loop = app.loop
    myip = app['myip']
    session = await get_session(request)
    params = dict(request.query)
    sleep = int(params.pop('sleep')) if 'sleep' in params else 0
    count = params.get('count',None)
    if not session.get('exclude_ip'):
        session['exclude_ip'] = {}
    proxy_list = []
    checked_exclude_ip = {}
    while True:
        exclude_ip = {}
        select_num = int(count) - len(proxy_list) if count is not None else None
        #需要每次都初始化，来检查时间
        session_exclude_ip = {ip: starttime for ip, starttime in session['exclude_ip'].items() if round(time.time() - starttime) < sleep}
        #合并session中的ip和刚刚通过检查的ip，用于数据库操作
        exclude_ip.update(session_exclude_ip)
        exclude_ip.update(checked_exclude_ip)
        data_list = await loop.run_in_executor(app['executor'], sqlhelper.select, select_num, params,exclude_ip)
        future_list = [check_proxy_effectivity_server(myip, data, app['executor']) for data in data_list]   # data: ('101.96.11.5', 80, 10, 0, 0)
        for future in asyncio.as_completed(future_list):
            proxy = await future
            if proxy:  # {'ip': '101.96.11.5', 'port': 80, 'protocol': 0, 'types': 0, 'speed': 0.26}
                checked_exclude_ip[proxy['ip']] = None
                proxy_list.append(proxy)
        exclude_ip.update(checked_exclude_ip)   #在session中加上通过检查的ip
        if count is None or len(proxy_list) >= int(count) or int(count) >= len(data_list) + len(exclude_ip):
            break
        else:
            await asyncio.sleep(0.5)
    #统一添加获取时间
    _time = time.time()
    for ip,starttime in exclude_ip.items():
        if starttime is None:
            exclude_ip[ip] = _time

    session['exclude_ip'] = exclude_ip  #if not do this,session won't set
    return web.json_response(data=proxy_list)


async def set_cookie(request):
    session = await get_session(request)
    session['session_id'] = str(uuid.uuid1())
    return web.json_response(data=dict(session))

async def get_cookie(request):
    session = await get_session(request)
    print(request.cookies)
    # if not session.get('proxy_list'):
    #     session['proxy_list'] = [1,2,3]
    # proxy_list = session['proxy_list']
    # print(proxy_list)

    return web.json_response(data=dict(session))


if __name__ == '__main__':
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor() as process:
        process.submit(start_api_server)
