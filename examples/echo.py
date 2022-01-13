import dataclasses
import json
from dataclasses import dataclass

from pyreapi.application import Scope, Pyre
from pyreapi.injector import Injector
from pyreapi.request import Request
from pyreapi.router import Router
from pyreapi.serializer import TextSerializer, JSONSerializer


@dataclass
class Body:
    a: int
    b: str
    c: dict

    @classmethod
    def from_request(cls, request: "Request"):
        d = json.loads(request.body)
        return cls(**d)


injector = Injector()
injector.register(Body, Body.from_request)
router = Router(serializer=JSONSerializer(), injector=injector)


@router.get("/")
async def a():
    return {"result": "test"}


@router.get("/text")
async def b(r: Request):
    r.response.serializer = TextSerializer()
    return {"result": r}


@router.post("/body")
async def c(body: Body):
    return {"body": dataclasses.asdict(body)}


if __name__ == "__main__":
    import uvicorn

    pyre = Pyre(router=router)
    uvicorn.run(pyre)
