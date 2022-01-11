import dataclasses
import inspect
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypedDict, Optional, Any, Callable


class Scope(TypedDict):
    method: str
    path: str


@dataclass
class RouteResponse:
    body: Optional[bytes]
    status: int = 200
    headers: dict = field(default_factory=dict)


@dataclass
class Body:
    a: int
    b: str
    c: dict

    @classmethod
    def from_request(cls, request: "Request"):
        d = json.loads(request.body)
        return cls(**d)


class Serializer(ABC):
    @abstractmethod
    def __call__(self, obj: Any) -> bytes:
        pass

    @abstractmethod
    def content_type(self):
        pass


class Response:
    def __init__(self, serializer: Serializer):
        self.serializer = serializer
        self.status = 200


class Request:
    def __init__(self, body: bytes, response: Response):
        self.response = response
        self.body = body


class TextSerializer(Serializer):
    def __call__(self, obj: Any) -> bytes:
        return str(obj).encode()

    def content_type(self):
        return "text"


class JSONSerializer(Serializer):
    def __call__(self, obj: Any) -> bytes:
        return json.dumps(obj).encode()

    def content_type(self):
        return "application/json"


class DependencyInjector(ABC):
    @abstractmethod
    def __call__(self, fn: Callable, request: Request):
        pass


class Injector(DependencyInjector):
    def __init__(self):
        self.parsers: dict[type, Callable[[Request], Any]] = self.default_parsers()

    @staticmethod
    def default_parsers():
        return {Request: lambda r: r}

    def register(self, typ: type, parser):
        self.parsers[typ] = parser

    def __call__(self, fn: Callable, request: Request):
        kwargs = {}
        for name, v in inspect.signature(fn).parameters.items():
            parser = self.parsers[v.annotation]
            kwargs[name] = parser(request)

        return kwargs


class Router:
    def __init__(self, *, serializer: Serializer, injector: DependencyInjector):
        self.serializer = serializer
        self.injector = injector
        self.handlers = {}

    def get(self, path):
        return self._decorate("GET", path)

    def post(self, path):
        return self._decorate("POST", path)

    def handle(self, method, path, body) -> RouteResponse:
        request = Request(body=body, response=Response(serializer=self.serializer))
        handler = self.handlers[(method, path)]
        r = handler(**self.injector(handler, request))

        return RouteResponse(
            body=request.response.serializer(r),
            status=request.response.status,
            headers={"content-type": request.response.serializer.content_type()},
        )

    def _decorate(self, method, path):
        def decorator(fn):
            self.handlers[(method, path)] = fn
            return fn

        return decorator


injector = Injector()
injector.register(Body, Body.from_request)
router = Router(serializer=JSONSerializer(), injector=injector)


@router.get("/")
def a():
    return {"result": "test"}


@router.get("/text")
def b(r: Request):
    r.response.serializer = TextSerializer()
    return {"result": r}


@router.post("/body")
def c(body: Body):
    return {"body": dataclasses.asdict(body)}


async def application(scope: Scope, receive, send):
    event = await receive()
    if event["type"] == "http.request":
        r = router.handle(scope["method"], scope["path"], event["body"])
        await send(
            {
                "type": "http.response.start",
                "status": r.status,
                "headers": list(r.headers.items()),
            }
        )
        await send({"type": "http.response.body", "body": r.body, "more_body": False})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(application)
