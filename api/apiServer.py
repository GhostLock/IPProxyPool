from aiohttp import web
from aiohttp.web import Request

def start_api_server():
    app = web.Application()
    app.add_routes([
        web.get('/', get)
    ])
    web.run_app(app, port=8000)


def step_routes(app):
    app.router.add_get("/", get)


async def get(request):
    data = {'data':request.url.path}

    return web.json_response(data,headers=None)


urls = (
    '/', 'select',
    '/delete', 'delete'
)

if __name__ == '__main__':
    start_api_server()
