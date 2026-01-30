import asyncio

from remotivelabs.broker import BrokerClient, FrameInfo


async def main() -> None:
    async with BrokerClient(url="http://127.0.0.1:50051") as broker_client:
        # list all available frames in the "DriverCan" namespace
        frame_infos: list[FrameInfo] = await broker_client.list_frame_infos("DriverCan")

        # simply print all frames and their signals
        for frame_info in frame_infos:
            print(f"{frame_info.name}")
            for signal_info in frame_info.signals.values():
                print(f"  {signal_info.name}")


if __name__ == "__main__":
    asyncio.run(main())
