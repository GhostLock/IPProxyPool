import asyncio
import sys
from aiohttp import web
from concurrent.futures import ThreadPoolExecutor

import config
from db.DataStore import sqlhelper


def start_api_server():
    app = init_app()
    windows_support(app)
    init_executor(app)
    web.run_app(app, host=config.HOST, port=config.PORT)


def init_app():
    app = web.Application()
    setup_routes(app)
    # app.on_startup.append(windows_support)
    # app.on_startup.append(init_executor)      #todo 使用多进程运行时signal为什么会报错?
    # app.on_cleanup.append(clean_executor)
    return app


def windows_support(app):
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        app._set_loop(loop)      #todo 这行代码是否有必要存在?


def init_executor(app):
    executor = ThreadPoolExecutor(max_workers=config.SERVER_EXECUTOR_NUM)
    app['executor'] = executor


def clean_executor(app):
    app['executor'].shutdown(wait=True)


def setup_routes(app):
    app.add_routes([
        web.get('/', select),
        web.get('/delete', delete),
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

def test():
    print("test")

if __name__ == '__main__':
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor() as process:
        process.submit(start_api_server)

