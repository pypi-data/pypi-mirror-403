import asyncio
from typing import Any

import aiofiles
import aiohttp
import httpx
import orjson
from httpx import AsyncClient

from beni.bdefine import MB

from . import bpath
from .btype import Null, XPath


async def getBytes(
    url: str,
    *,
    headers: dict[str, Any] = Null,
    timeout: int = 10,
):
    async with AsyncClient() as client:
        client.headers.update(headers)
        client.timeout = timeout
        response = await client.get(url)
        return response.content


async def getStr(
    url: str,
    *,
    encoding: str = 'UTF8',
    headers: dict[str, Any] = Null,
    timeout: int = 10,
):
    data = await getBytes(url, headers=headers, timeout=timeout)
    return data.decode(encoding)


async def getJson(
    url: str,
    *,
    headers: dict[str, Any] = Null,
    timeout: int = 10,
):
    data = await getBytes(url, headers=headers, timeout=timeout)
    return orjson.loads(data)


async def postBytes(
    url: str,
    *,
    data: bytes | dict[str, Any] = Null,
    headers: dict[str, Any] = Null,
    timeout: int = 10,
):
    async with AsyncClient() as client:
        client.headers.update(headers)
        client.timeout = timeout
        response = await client.post(url, json=data)
        return response.content


async def postStr(
    url: str,
    *,
    encoding: str = 'UTF8',
    data: bytes | dict[str, Any] = Null,
    headers: dict[str, Any] = Null,
    timeout: int = 10,
):
    data = await postBytes(url, data=data, headers=headers, timeout=timeout)
    return data.decode(encoding)


async def postJson(
    url: str,
    *,
    data: bytes | dict[str, Any] = Null,
    headers: dict[str, Any] = Null,
    timeout: int = 10,
):
    data = await postBytes(url, data=data, headers=headers, timeout=timeout)
    return orjson.loads(data)


async def download(url: str, file: XPath, timeout: int = 300, headers: dict[str, Any] = Null):
    try:
        file = bpath.get(file)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                bpath.make(file.parent)
                sizeLoaded = 0
                async with aiofiles.open(file, 'wb') as f:
                    while True:
                        data = await response.content.read(1 * MB)
                        if data:
                            await f.write(data)
                            sizeLoaded += len(data)
                        else:
                            if 'Content-Encoding' not in response.headers:
                                assert response.content_length, '下载内容为空'
                                assert response.content_length == sizeLoaded, '下载为文件不完整'
                            break
    except Exception as e:
        if str(e) == 'Timeout context manager should be used inside a task':
            # 特殊情况，在 btask 环境中使用 aiohttp 会报这个错，只能用同步方式下载
            await downloadSyncInExecutor(url, file, timeout, headers)
        else:
            bpath.remove(file)
            raise


def downloadSync(url: str, file: XPath, timeout: int = 300, headers: dict[str, Any] = Null):
    """
    使用 httpx 同步流式下载大文件。
    """
    file = bpath.get(file)
    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()
                bpath.make(file.parent)
                sizeLoaded = 0
                with open(file, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=MB):
                        if chunk:
                            f.write(chunk)
                            sizeLoaded += len(chunk)
                # 检查完整性（未压缩时）
                if 'Content-Encoding' not in response.headers:
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        assert int(content_length) == sizeLoaded, '下载为文件不完整'
                    else:
                        assert sizeLoaded > 0, '下载内容为空'
    except:
        bpath.remove(file)
        raise


async def downloadSyncInExecutor(url: str, file: XPath, timeout: int = 300, headers: dict[str, Any] = Null):
    '使用 run_in_excutor 实现的异步下载，性能较差，只用在 btask 环境中'
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, downloadSync, url, file, timeout, headers)
