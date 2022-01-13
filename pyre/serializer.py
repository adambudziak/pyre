import json
from abc import ABC, abstractmethod
from typing import Any


class Serializer(ABC):
    @abstractmethod
    def __call__(self, obj: Any) -> bytes:
        pass

    @abstractmethod
    def content_type(self):
        pass


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
