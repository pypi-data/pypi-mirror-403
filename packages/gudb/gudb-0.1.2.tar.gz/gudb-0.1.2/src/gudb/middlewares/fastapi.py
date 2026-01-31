from typing import Callable, Awaitable, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from gudb import gudb
import time

class SafeDBMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware for gudb.
    Currently monitors request duration. 
    Note: Real SQL interception happens at the DB driver level via gudb.monitor(conn).
    """
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # We can inject context into the request or simply log the start
        start_time = time.perf_counter()
        
        # Attach gudb to request state for use in internal logic
        request.state.gudb = gudb
        
        response = await call_next(request)
        
        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Database-Guardian-Time"] = f"{process_time:.2f}ms"
        
        return response
