import asyncio

async def task1():
    await asyncio.sleep(1)
    print("task1 done")

async def main():
    await task1()   # 直接 await
    print("main done")

asyncio.run(main())
