import asyncio
from typing import AsyncIterator

from remotivelabs.broker import BrokerClient, Frame, FrameInfo
from remotivelabs.broker.filters import ReceiverFilter


async def main() -> None:
    async with BrokerClient(url="http://127.0.0.1:50051") as broker_client:
        # list frames in the "DriverCan" namespace
        frame_infos: list[FrameInfo] = await broker_client.list_frame_infos("DriverCan")

        # filter according to some critera
        filtered_frame_infos = list(filter(ReceiverFilter(ecu_name="ECU2"), frame_infos))

        # subscribe using the filtered frame infos
        stream: AsyncIterator[Frame] = await broker_client.subscribe_frames(
            ("DriverCan", filtered_frame_infos),
        )

        # will receive frames until stream is closed by broker or an error occurs
        async for frame in stream:
            print(f"Received frame: {frame}")


if __name__ == "__main__":
    asyncio.run(main())
