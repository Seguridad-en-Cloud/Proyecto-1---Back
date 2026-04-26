import asyncio
from sqlalchemy.util._concurrency_py3k import await_only, greenlet_spawn

async def main():
    async def _getconn():
        loop1 = asyncio.get_running_loop()
        await asyncio.sleep(0)
        loop2 = asyncio.get_running_loop()
        return loop1 is loop2

    def sync_call():
        return await_only(_getconn())

    res = await greenlet_spawn(sync_call)
    print("Loops match:", res)

asyncio.run(main())
