# NanoServer

**Zero-dependency HTTP API server built on Python's stdlib.** Simple, fast, pure Python.

```python
from nanoserver import APIServer

server = APIServer(host="0.0.0.0", port=8000)
server.add_route('GET', '/', lambda req: {"message": "Hello World"})
server.run()
```

No Flask. No FastAPI. No dependencies. Just Python.

## Install

**With pip:**
```bash
pip install nanoserver
```

**With uv:**
```bash
uv add nanoserver
```

## Quick Start

```python
from nanoserver import APIServer

server = APIServer(port=8000)

# GET endpoint
def home(req):
    return {"message": "Hello World!"}

def hello(req):
    return {"message": "This is hello view."}

# POST endpoint
def echo(req, data):
    return {"received": data}

server.add_route('GET', '/', home)
server.add_route('GET', '/hello', hello)
server.add_route('POST', '/echo', echo)

server.run()
```

Test it:
```bash
curl http://localhost:8000/hello
curl -X POST http://localhost:8000/echo -d '{"test":"data"}' -H "Content-Type: application/json"
```

## Other Usage Examples

### Simple API

```python
from nanoserver import APIServer

server = APIServer(port=8000)

def get_status(req):
    return {"status": "running", "version": "1.0"}

def create_item(req, data):
    return {"created": data, "id": 123}

server.add_route('GET', '/status', get_status)
server.add_route('POST', '/items', create_item)

server.run()
```

### Webhook Receiver

```python
from nanoserver import APIServer

server = APIServer(port=9000)

def handle_webhook(req, data):
    print(f"Received: {data}")
    # Process your webhook
    return {"status": "received"}

server.add_route('POST', '/webhook', handle_webhook)
server.run()
```

### Mock API for Testing

```python
from nanoserver import APIServer

server = APIServer(port=3000)

def get_user(req):
    return {"id": 1, "name": "John", "email": "john@example.com"}

def login(req, data):
    if data.get('password') == 'secret':
        return {"token": "abc123"}
    return {"error": "Invalid"}

server.add_route('GET', '/user', get_user)
server.add_route('POST', '/login', login)

server.run()
```

### Inference API for Local LLM

```python
from nanoserver import APIServer
from your_local_model_loader import model

server = APIServer(port=3000)


def inference(req, data):
    prompt = data.get('prompt')
    temperature = data.get('temperature')
    max_tokens = data.get('max_tokens')
    try:
        completion = model.create_chat_completion(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        
        return completion
    except Exception as exc:
        raise exc

server.add_route('POST', '/inference', inference)

server.run()
```

## Why NanoServer?

- **🪶 Lightweight** - Pure Python stdlib, no dependencies
- **⚡ Fast** - Running in miliseconds
- **🎯 Simple** - One class, two methods, done
- **🔧 Flexible** - Microservices, IoT, prototypes, webhooks

Perfect for quick APIs, prototypes, testing, and environments where you can't install heavy frameworks.

## API

### `APIServer(host='0.0.0.0', port=8000)`
Create server instance.

### `server.add_route(method, path, handler)`
Register a route. `method` is `'GET'` or `'POST'`.

### `server.run()`
Start the server.

---

## Contributing

Found a bug? Want a feature? PRs welcome!

**Made with ❤️ for developers who love simplicity (by [Taufiq](https://taufiq.cc))**
