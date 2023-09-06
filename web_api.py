#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


# pip install aiohttp
from aiohttp import web

from add_notify import add_notify
from config import HOST, PORT
from common import TypeEnum


routes = web.RouteTableDef()


def process_notify(data: dict):
    name = data["name"]
    message = data["message"]
    type = data.get("type", TypeEnum.INFO)
    url = data.get("url")

    has_delete_button = data.get("has_delete_button", False)  # Из json поле будет булевым
    if isinstance(has_delete_button, str):
        has_delete_button = has_delete_button == "true"

    show_type = data.get("show_type", True)  # Из json поле будет булевым
    if isinstance(show_type, str):
        show_type = show_type == "true"

    group = data.get("group")
    group_max_number = data.get("group_max_number")
    if group_max_number and not isinstance(group_max_number, int):
        group_max_number = int(group_max_number)

    need_html_escape_content = data.get("need_html_escape_content", True)
    if isinstance(need_html_escape_content, str):
        need_html_escape_content = need_html_escape_content == "true"

    add_notify(
        name=name,
        message=message,
        type=type,
        url=url,
        has_delete_button=has_delete_button,
        show_type=show_type,
        group=group,
        group_max_number=group_max_number,
        need_html_escape_content=need_html_escape_content,
    )


@routes.get("/")
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
    
    <fieldset>
        <legend>Has delete button:</legend>
        <div>
            <input id="has_delete_button_true" name="has_delete_button" type="radio" value="true"/>
            <label for="has_delete_button_true">Yes</label>
            
            <input id="has_delete_button_false" name="has_delete_button" type="radio" value="false" checked/>
            <label for="has_delete_button_false">No</label>
        </div>
    </fieldset>
    
    <fieldset>
        <legend>Show type:</legend>
        <div>
            <input id="show_type_true" name="show_type" type="radio" value="true" checked/>
            <label for="show_type_true">Show</label>
            
            <input id="show_type_false" name="show_type" type="radio" value="false"/>
            <label for="show_type_false">Hide</label>
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
    
    <fieldset>
        <legend>Need html escape content:</legend>
        <div>
            <input id="need_html_escape_content_true" name="need_html_escape_content" type="radio" value="true" checked/>
            <label for="need_html_escape_content_true">Yes</label>
            
            <input id="need_html_escape_content_false" name="need_html_escape_content" type="radio" value="false"/>
            <label for="need_html_escape_content_false">No</label>
        </div>
    </fieldset>
    <br/>
    
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

    return web.Response(text=text, content_type="text/html")


@routes.post("/add_notify")
async def add_notify_handler(request: web.Request):
    try:
        data = await request.post()
        if not data:
            data = await request.json()

        print(f"[add_notify] data: {data}")
        process_notify(data)

        return web.json_response({"ok": True})

    except Exception as e:
        return web.json_response({"error": str(e)})


if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)

    web.run_app(app, host=HOST, port=PORT)
