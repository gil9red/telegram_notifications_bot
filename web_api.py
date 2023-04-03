#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


# pip install aiohttp
from aiohttp import web

from add_notify import add_notify
from config import HOST, PORT
from common import TypeEnum


routes = web.RouteTableDef()


def process_notify(data: dict):
    name = data['name']
    message = data['message']
    type = data.get('type', TypeEnum.INFO)
    url = data.get('url')

    has_delete_button = data.get('has_delete_button', False)  # Из json поле будет булевым
    if isinstance(has_delete_button, str):
        has_delete_button = has_delete_button == 'true'

    show_type = data.get('show_type', True)  # Из json поле будет булевым
    if isinstance(show_type, str):
        show_type = show_type == 'true'

    group = data.get('group')
    group_max_number = data.get('group_max_number')
    if group_max_number and not isinstance(group_max_number, int):
        group_max_number = int(group_max_number)

    add_notify(
        name=name,
        message=message,
        type=type,
        url=url,
        has_delete_button=has_delete_button,
        show_type=show_type,
        group=group,
        group_max_number=group_max_number,
    )


@routes.get('/')
async def index(_: web.Request):
    text = """
<form action="/add_notify" method="post" accept-charset="utf-8"
    <p>
        <label for="name">Name:</label>
        <input id="name" name="name" type="text" value="test_web_api" autofocus/>
    <p/>
    <p>
        <label for="message">Message:</label>
        <input id="message" name="message" type="text" value="BUGAGA! Привет мир!"/>
    </p>
    <p>
        <label for="url">Url:</label>
        <input id="url" name="url" type="url" value=""/>
    </p>
    <p>
        <label for="has_delete_button">Has delete button:</label>
        <input id="has_delete_button" name="has_delete_button" type="checkbox" value="true"/>
    </p>
    <fieldset>
        <legend>Show type:</legend>
        <div>
            <input id="show_type_true" name="show_type" type="radio" value="true" checked/>
            <label for="show_type_true">Show</label>
            
            <input id="show_type_hide" name="show_type" type="radio" value="false"/>
            <label for="show_type_hide">Hide</label>
        </div>
    </fieldset>
    
    <fieldset>
        <legend>Group:</legend>
        <p>
            <label for="group">Name:</label>
            <input id="group" name="group" type="text" value=""/>
        </p>
        <p>
            <label for="group_max_number">Max number:</label>
            <input id="group_max_number" name="group_max_number" type="number" value=""/>
        </p>
    </fieldset>
    
    <input type="submit"/>
    <br/>
    <div id="result"></div>
</form>
<script>
document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('form').addEventListener('submit', function (event) {
        let data = this;
        fetch(data.getAttribute('action'), {
            method: data.getAttribute('method'),
            body: new FormData(data)
        })
            .then(res => res.text())
            .then(function (data) {
                document.querySelector('#result').textContent = data;
            })
        ;
        event.preventDefault();
    });
});
</script>
    """

    return web.Response(text=text, content_type='text/html')


@routes.post('/add_notify')
async def add_notify_handler(request: web.Request):
    try:
        data = await request.post()
        if not data:
            data = await request.json()

        print(f'[add_notify] data: {data}')
        process_notify(data)

        return web.json_response({'ok': True})

    except Exception as e:
        return web.json_response({'error': str(e)})


if __name__ == '__main__':
    app = web.Application()
    app.add_routes(routes)

    web.run_app(
        app,
        host=HOST, port=PORT
    )
