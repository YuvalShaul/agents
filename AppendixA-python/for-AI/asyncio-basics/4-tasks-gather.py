
import asyncio

async def say(what, when):
    await asyncio.sleep(when)
    print(f'  {what} {when}')
    return when


async def main():
    task1 = asyncio.create_task(say('hello', 5))
    task2 = asyncio.create_task(say('goodbye', 5))
    results = await asyncio.gather(
        task1,
        task2
    )
    print(results)


loop = asyncio.new_event_loop()  # DOES NOT CREATE A LOOP
loop.run_until_complete(main())  # Loop born and dies



