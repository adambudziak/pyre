import inspect
from abc import ABC, abstractmethod
from typing import Callable, Any

from pyreapi.request import Request


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
