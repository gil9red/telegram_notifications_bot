#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# pip install aiohttp
from aiohttp import web

from add_notify import add_notify
from config import HOST, PORT
from common import TypeEnum


routes = web.RouteTableDef()


@routes.get('/')
async def index(request: web.Request):
    text = """
<form action="/add_notify" method="post" accept-charset="utf-8"
    <p>
        <label for="name">Name:</label>
        <input id="name" name="name" type="text" value="test_web_api" autofocus/>
    <p/>
    <p>
        <label for="message">Message:</label>
        <input id="message" name="message" type="message" value="BUGAGA! Привет мир!"/>
    </p>
    <p>
        <label for="url">Url:</label>
        <input id="url" name="url" type="url" value=""/>
    </p>
    <p>
        <label for="has_delete_button">Has delete button:</label>
        <input id="has_delete_button" name="has_delete_button" type="checkbox" value="true"/>
    </p>
    <input type="submit"/>
</form> 
    """

    return web.Response(text=text, content_type='text/html')


@routes.post('/add_notify')
async def add_notify_handler(request: web.Request):
    data = await request.post()
    if not data:
        data = await request.json()

    print(f'[add_notify] data: {data}')

    name = data['name']
    message = data['message']
    type = data.get('type', TypeEnum.INFO)
    url = data.get('url')
    has_delete_button = data.get('has_delete_button', False)  # Из json поле будет булевым
    if isinstance(has_delete_button, str):
        has_delete_button = has_delete_button == 'true'

    add_notify(
        name=name,
        message=message,
        type=type,
        url=url,
        has_delete_button=has_delete_button,
    )

    return web.json_response({'ok': True})


app = web.Application()
app.add_routes(routes)

web.run_app(
    app,
    host=HOST, port=PORT
)
