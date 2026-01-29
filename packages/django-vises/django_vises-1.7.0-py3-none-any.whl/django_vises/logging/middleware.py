import os
import urllib.parse
from logging import getLogger

import logfire


class ASGIMiddlewareAccessLogging:
    logfire: bool = False

    def __init__(self, app, remote_addr_header_name: str = "X-Forwarded-For") -> None:
        self.logger = getLogger("ASGI")
        self.app = app
        # X-Forwarded-For/X-Real-IP
        self.remote_addr_header_name = remote_addr_header_name.lower().encode("latin1")

        # init logfire
        logfire_token = os.getenv("LOGFIRE_TOKEN")
        if logfire_token:
            logfire.configure(token=logfire_token)
            self.logfire = True

    async def __call__(self, scope, receive, send) -> None:
        data = dict()
        data["response"] = {"status": 500}

        async def inner_send(message) -> None:
            if message["type"] == "http.response.start":
                data["response"] = message
            await send(message)

        try:
            # info["start_time"] = time.time()
            await self.app(scope, receive, inner_send)
        except Exception as e:
            # info["response"]["status"] = 500

            raise e
        finally:
            # info["end_time"] = time.time()
            pass

        if scope["type"] != "http":
            return

        headers = scope.get("headers")
        headers = dict(headers)

        remote_addr = self._get_remote_addr(scope, headers)
        user_agent = headers.get(b"user-agent", b"").decode("utf-8")

        request_method = scope.get("method")
        request_path = scope.get("path")
        request_query_string = scope.get("query_string")
        if request_query_string:
            request_path += urllib.parse.unquote(request_query_string)

        status_code = data["response"].get("status")

        self.logger.info(
            f'{remote_addr} - "{request_method} {request_path}" {status_code}'
        )

        if self.logfire:
            logfire.info(
                f"{remote_addr} {request_method} {request_path}",
                remote_addr=remote_addr,
                request_method=request_method,
                request_path=request_path,
                status_code=status_code,
                user_agent=user_agent,
            )

    def _get_remote_addr(self, scope, headers: dict) -> str:
        remote_addr = headers.get(self.remote_addr_header_name, b"").decode("latin1")

        if remote_addr:
            return remote_addr

        remote_addr = scope.get("client")
        if remote_addr:
            return f"{remote_addr[0]}:{remote_addr[1]}"

        return "-"
