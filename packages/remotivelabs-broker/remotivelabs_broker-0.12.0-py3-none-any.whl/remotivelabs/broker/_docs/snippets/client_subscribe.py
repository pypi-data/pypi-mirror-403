import asyncio
from typing import AsyncIterator

from remotivelabs.broker import BrokerClient, Frame


async def main() -> None:
    async with BrokerClient(url="http://127.0.0.1:50051") as broker_client:
        # subscribe to a frame named "EngineData" (including all its signals) in the "DriverCan" namespace
        stream: AsyncIterator[Frame] = await broker_client.subscribe_frames(
            ("DriverCan", ["EngineData"]),
        )

        # will receive frames until stream is closed by broker or an error occurs
        async for frame in stream:
            print(f"Received frame: {frame}")


if __name__ == "__main__":
    asyncio.run(main())
