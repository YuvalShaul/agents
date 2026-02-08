
import asyncio

async def say(what, when):
    await asyncio.sleep(when)
    print(what)

# WITHOUT TASKS
print('WITHOUT TASKS')

asyncio.run(say('hello', 5))   # Loop born and dies
asyncio.run(say('goodbye', 5))   # Loop born and dies

# WITH TASKS
print('WITH TASKS')
async def main():
    task1 = asyncio.create_task(say('hello', 5))
    task2 = asyncio.create_task(say('goodbye', 5))
    await task1
    await task2 


loop = asyncio.new_event_loop()  # DOES NOT CREATE A LOOP
loop.run_until_complete(main())  # Loop born and dies



