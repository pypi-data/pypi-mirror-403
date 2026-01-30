import asyncio

from remotivelabs.broker.recording_session import RecordingSessionClient


async def main() -> None:
    # Create a recording session client
    async with RecordingSessionClient(url="http://127.0.0.1:50051") as rs_client:
        # List available recording files on the broker
        files = await rs_client.list_recording_files()
        print(f"Available recording files: {files}")

        # open a recording session with the first file
        rs_ref = rs_client.get_session(str(files[0]))
        async with rs_ref as session:
            # start playback
            status = await session.play()
            print(f"Playback started with status: {status}")

        # exiting the async with block will close the session, but playback will continue if other sessions are open


if __name__ == "__main__":
    asyncio.run(main())
