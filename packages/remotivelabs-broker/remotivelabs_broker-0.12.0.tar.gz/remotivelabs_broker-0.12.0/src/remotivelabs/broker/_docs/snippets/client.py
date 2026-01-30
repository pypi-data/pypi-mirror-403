import asyncio

from remotivelabs.broker import BrokerClient


async def main() -> None:
    # Create a BrokerClient instance and list all namespaces available on that broker.
    async with BrokerClient(url="http://127.0.0.1:50051") as broker_client:
        ns = await broker_client.list_namespaces()
        print(f"Namespaces: {ns}")


if __name__ == "__main__":
    asyncio.run(main())
