from pyre.serializer import Serializer


class Response:
    def __init__(self, serializer: Serializer):
        self.serializer = serializer
        self.status = 200


class Request:
    def __init__(self, body: bytes, response: Response):
        self.response = response
        self.body = body
