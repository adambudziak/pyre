from dataclasses import dataclass, field
from typing import Optional

from pyre.injector import DependencyInjector
from pyre.request import Request, Response
from pyre.serializer import Serializer


class Router:
    def __init__(self, *, serializer: Serializer, injector: DependencyInjector):
        self.serializer = serializer
        self.injector = injector
        self.handlers = {}

    def get(self, path):
        return self._decorate("GET", path)

    def post(self, path):
        return self._decorate("POST", path)

    async def handle(self, method, path, body) -> "RouteResponse":
        request = Request(body=body, response=Response(serializer=self.serializer))
        handler = self.handlers[(method, path)]
        r = await handler(**self.injector(handler, request))

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


@dataclass
class RouteResponse:
    body: Optional[bytes]
    status: int = 200
    headers: dict = field(default_factory=dict)
