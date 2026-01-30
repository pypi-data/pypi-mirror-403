import asyncio

from remotivelabs.broker import BrokerClient
from remotivelabs.broker.restbus import RestbusFrameConfig, RestbusSignalConfig


async def main() -> None:
    async with BrokerClient(url="http://127.0.0.1:50051") as broker_client:
        # Start the restbus on the "DriverCan" namespace with one frame configuration
        await broker_client.restbus.add(
            ("DriverCan", [RestbusFrameConfig(name="EngineData")]),
            start=True,
        )

        # now update some of its signals
        signal_configs: list[RestbusSignalConfig] = [
            RestbusSignalConfig.set(name="EngineData.EngineRpm", value=1500),
            RestbusSignalConfig.set(name="EngineData.EngineTemp", value=90),
        ]
        await broker_client.restbus.update_signals(
            ("DriverCan", signal_configs),
        )


if __name__ == "__main__":
    asyncio.run(main())
