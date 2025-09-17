from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
import uvicorn

from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport

# 创建 MCP Server
server = Server(name="remote-server", version="1.0.0")

# SSE Transport：注意传 endpoint 字符串
sse = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        # 运行 MCP server
        await server.run(streams[0], streams[1], server.create_initialization_options())
    return Response()  # 避免 NoneType 错误

routes = [
    Route("/mcp", endpoint=handle_sse, methods=["GET"]),
    Mount("/messages/", app=sse.handle_post_message),
]

app = Starlette(routes=routes)

if __name__ == "__main__":
    print("MCP server listening on port 3000")
    uvicorn.run(app, host="127.0.0.1", port=3000)

