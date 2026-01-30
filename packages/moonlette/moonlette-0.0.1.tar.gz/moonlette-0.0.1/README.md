# moonlette

A simple web server with websockets support based on starlette, uvicorn and authlib.

## Installation

```
pip install moonlette
```

## Example usage (http)

```
from mooonlette.server import Server
server = Server(port=8081, host="localhost")
      
def handler(path, headers, path_parameters, query_parameters, request_body):
    return (200, b"It Worked!", "text/plain", {})

server.attach_handler("GET", "/test", handler)
server.run()
```

## Example usage (websocckets)

Coming soon

## Documentation

Coming Soon