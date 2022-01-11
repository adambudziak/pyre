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


class Request:
    def __init__(self, response: Response):
        self.response = response


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
    def __call__(self, fn: Callable, request: Request):
        kwargs = {}
        for name, v in inspect.signature(fn).parameters.items():
            if issubclass(v.annotation, Request):
                kwargs[name] = request

        return kwargs


class Router:
    def __init__(self, *, serializer: Serializer, injector: DependencyInjector):
        self.serializer = serializer
        self.injector = injector
        self.handlers = {}

    def get(self, path):
        def decorator(fn):
            self.handlers[("GET", path)] = fn
            return fn

        return decorator

    def handle(self, method, path) -> RouteResponse:
        request = Request(response=Response(serializer=self.serializer))
        handler = self.handlers[(method, path)]
        r = handler(**self.injector(handler, request))
        return RouteResponse(
            body=request.response.serializer(r),
            status=200,
            headers={"content-type": request.response.serializer.content_type()},
        )


router = Router(serializer=JSONSerializer(), injector=Injector())


@router.get("/")
def a():
    return {"result": "dupa"}


@router.get("/text")
def a(r: Request):
    r.response.serializer = TextSerializer()
    return {"result": r}


async def application(scope: Scope, receive, send):
    event = await receive()
    if event["type"] == "http.request":
        r = router.handle(scope["method"], scope["path"])
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
