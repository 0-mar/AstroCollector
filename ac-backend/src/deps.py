from fastapi import Request
import httpx
from redis.asyncio import Redis


def get_async_http_client(request: Request) -> httpx.AsyncClient:
    return request.state.async_http_client


def get_sync_http_client(request: Request) -> httpx.Client:
    return request.state.sync_http_client


def get_redis_client(request: Request) -> Redis:
    return request.state.redis_client
