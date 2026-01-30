import asyncio

from remotivelabs.broker import BrokerClient
from remotivelabs.broker.secoc import SecocFreshnessValue


async def main() -> None:
    async with BrokerClient(url="http://127.0.0.1:50051") as broker_client:
        prop = SecocFreshnessValue(fv=b"\x00\x00\x12\x34")
        await broker_client.set_secoc_property(namespace="MyNamespace", property=prop)


if __name__ == "__main__":
    asyncio.run(main())
