#   Moonlette - a simple web server
#
#   MIT License - Copyright (C) 2026  Visual Topology Ltd
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software
#   and associated documentation files (the "Software"), to deal in the Software without
#   restriction, including without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#   BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import asyncio
import uuid
import contextlib
import urllib.parse
import mimetypes
import signal
import threading
import requests
import time

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse, HTMLResponse
from starlette.websockets import WebSocket
from starlette.routing import Route, WebSocketRoute
from starlette.middleware.sessions import SessionMiddleware

import logging
import uvicorn

class Server:

    def __init__(self, host="localhost", port=8889, startup_timeout_s=5, **kwargs):
        self.host = host
        self.port = port
        self.startup_timeout_s = startup_timeout_s
        self.configuration = kwargs
        self.redirects = []
        self.handlers = []
        self.handler_registry = {}
        self.ws_handlers = []
        self.default_handlers = {}
        self.app = None
        self.loop = None
        self.is_running = False
        self.logger = logging.getLogger("moonlette.server")
        self.attach_handler("GET", "/moonlette_status", lambda *args: (200, b"OK", "text/plain", {}))

    def get_ws_handlers(self):
        return self.ws_handlers

    def get_http_handlers(self):
        return self.handlers

    def get_redirects(self):
        return self.redirects

    def get_default_handlers(self):
        return self.default_handlers

    def add_redirect(self, from_path, to_path):
        self.redirects.append((from_path,to_path))

    def attach_handler(self, method, path, handler):
        handler_id = str(uuid.uuid4())
        t = (method, path, handler)
        self.handler_registry[handler_id] = t
        self.handlers.append(t)
        return handler_id

    def detach_handler(self, handler_id):
        t = self.handler_registry.get(handler_id, None)
        if t is not None:
            self.handlers.remove(t)

    def attach_ws_handler(self, path, handler):
        self.ws_handlers.append((path, handler))

    def attach_webroot(self, path_prefix, static_folder):

        def serve_static(path, headers, path_parameters, query_parameters, request_body):
            filepath = os.path.join(static_folder,path_parameters["path"])
            return self.serve_file(filepath)

        self.attach_handler("GET", path_prefix + "/$$path", serve_static)

    def serve_file(self, path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                (mimetype, encoding) = mimetypes.guess_type(path)
                content = f.read()
                return (200, content, mimetype, {})
        else:
            return (404, b"NOT FOUND", "text/plain", {})

    async def http_endpoint(self, request:Request, user=None):

        path = "/" + request.path_params["path"]

        headers = {k: v for (k, v) in request.headers.items()}
        if user is not None:
            headers["X-User-ID"] = user
        request_body = request.body
        redirects = self.get_redirects()
        for (from_path, to_path) in redirects:
            if path == from_path:
                return RedirectResponse(url=to_path)

        for (handlermethod, handlerpath, handler) in self.get_http_handlers():
            if handlermethod.lower() != request.method.lower():
                continue
            path_parameters = {}

            if self.__match_path(handlerpath, path, path_parameters):

                try:
                    handled = handler(path, headers, path_parameters, request.query_params, request_body)
                    if handled:
                        (code, content, mimetype, custom_headers) = handled
                        return Response(content=content, status_code=code, media_type=mimetype,
                                        headers=custom_headers)

                except Exception as ex:
                    logging.exception("Exception while handling request")
                    return Response(status_code=500, content=str(ex), media_type="text/plain", headers={})
                break

        return Response(status_code=404, content="NOT FOUND", media_type="text/plain", headers={})

    async def websocket_endpoint(self, websocket: WebSocket, user=None):

        await websocket.accept()
        path = "/"+websocket.path_params["path"]

        headers = {k: v for (k, v) in websocket.headers.items()}
        if user is not None:
            headers["X-User-ID"] = user
        matched = False
        for (handlerpath, handler) in self.get_ws_handlers():
            path_parameters = {}
            if self.__match_path(handlerpath, path, path_parameters):
                matched = True
                executing_tasks = set()
                def sender(msg):
                    if msg is None:
                        async def close_ws():
                            await websocket.close()

                        task = self.loop.create_task(close_ws())
                    else:
                        async def send_ws():
                            if isinstance(msg, bytes):
                                await websocket.send_bytes(msg)
                            else:
                                await websocket.send_text(msg)

                        task = self.loop.create_task(send_ws())
                    task.add_done_callback(executing_tasks.discard)
                    executing_tasks.add(task)

                session_id = str(uuid.uuid4())
                session = handler(session_id, sender, path, path_parameters, websocket.query_params,
                                  headers)
                try:
                    async for message in websocket.iter_bytes():
                        if message != b"":
                            session.recv(message)
                        else:
                            pass  # heartbeat?
                except Exception as ex:
                    self.logger.exception("Exception while handling request")
                break
        if not matched:
            await websocket.close()

    def register_middleware(self, app):
        pass

    def run(self, callback):



        self.is_running = True

        @contextlib.asynccontextmanager
        async def lifespan(app):

            def check_running():
                url = f"http://{self.host}:{self.port}/moonlette_status"

                max_retries = 5
                retry_interval = self.startup_timeout_s
                for r in range(max_retries):
                    retry_interval /= 2

                retry = 0
                while retry < max_retries:
                    try:
                        time.sleep(retry_interval)
                        response = requests.get(url)
                        if response.status_code == 200:
                            self.is_running = True
                            if callback:
                                callback(True)
                            return
                    except:
                        pass
                    retry += 1
                    retry_interval *= 2
                if callback:
                    callback(False)

            t = threading.Thread(target=check_running)
            t.start()
            yield

        async def websocket_endpoint(ws:WebSocket):
            return await self.websocket_endpoint(ws)

        async def http_endpoint(request:Request):
            return await self.http_endpoint(request)

        self.app = Starlette(debug=True, routes=[
            WebSocketRoute("/{path:path}", websocket_endpoint),
            Route("/{path:path}", http_endpoint),
        ], lifespan=lifespan)

        self.loop = asyncio.new_event_loop()

        self.register_middleware(self.app)

        config = uvicorn.Config(self.app,port=self.port, log_level="info", loop=lambda : self.loop)
        self.server = uvicorn.Server(config)
        self.server.run()

    def close(self):
        self.server.handle_exit(signal.SIGINT,None)
        self.is_running = False
        self.logger.info('Closing ...')

    def check_running(self):
        return self.is_running

    def __match_path(self, handlerpath, path, parameters):
        handlerpathlist = handlerpath.split("/")
        pathlist = path.split("/")
        matched = self.__match(handlerpathlist,pathlist, parameters, True)
        if not matched:
            # if the match fails, clear away any data collected on a partial match
            parameters.clear()
        return matched

    def __match(self, handlerpathlist, pathlist, parameters,required):
        if handlerpathlist == [] and pathlist == []:
            return True
        if len(handlerpathlist) > 0 and not required:
            # allow empty match
            parameters1 = {}
            if self.__match(handlerpathlist[1:], pathlist, parameters1, True):
                parameters.update(parameters1)
                return True
        if handlerpathlist == [] or pathlist == []:
            return False

        matchexp = handlerpathlist[0]
        if matchexp.startswith("$$"):
            key = matchexp[2:]
            parameters[key] = pathlist[0]
            parameters1 = {}
            if self.__match(handlerpathlist, pathlist[1:], parameters1, False):
                parameters.update(parameters1)
                if key in parameters1:
                    parameters[key] = pathlist[0]+ "/" + parameters1[key]
                return True
            else:
                return False
        elif matchexp.startswith("$"):
            key = matchexp[1:]
            parameters[key] = pathlist[0]
        else:
            if matchexp != pathlist[0]:
                return False

        return self.__match(handlerpathlist[1:], pathlist[1:], parameters, True)

    def __collect_parameters(self, query, parameters):
        if query != "":
            qargs = query.split("&")
            for qarg in qargs:
                argsplit = qarg.split("=")
                if len(argsplit) == 2:
                    key = urllib.parse.unquote(argsplit[0])
                    value = urllib.parse.unquote(argsplit[1])
                    parameters[key] = value


