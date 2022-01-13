from typing import TypedDict

from pyreapi.router import Router


class Pyre:
    def __init__(self, router: Router):
        self.router = router

    async def __call__(self, scope: "Scope", receive, send):
        event = await receive()
        if event["type"] == "http.request":
            r = await self.router.handle(scope["method"], scope["path"], event["body"])
            await send(
                {
                    "type": "http.response.start",
                    "status": r.status,
                    "headers": list(r.headers.items()),
                }
            )
            await send(
                {"type": "http.response.body", "body": r.body, "more_body": False}
            )


class Scope(TypedDict):
    method: str
    path: str
