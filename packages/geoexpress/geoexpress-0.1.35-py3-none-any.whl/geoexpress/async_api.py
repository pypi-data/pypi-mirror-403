import asyncio
from geoexpress.core.encoder import encode


async def encode_async(input: str, output: str, options=None):
    return await asyncio.to_thread(
        encode,
        input,
        output,
        options
    )
