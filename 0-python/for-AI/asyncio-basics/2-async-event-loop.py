
import asyncio

async def say(what, when):
    loop = asyncio.get_event_loop()
    print("Inside async func, event loop: ", loop)
    await asyncio.sleep(when)
    print(what)

# I could call get_event_loop() and get the same event loop, but this behaviour may change in the future.
# # loop = asyncio.get_event_loop()
# The get_event_loop() function will create an event loop, but only for the main thread, and this behaviour may change in the future.

# But I could also create a new event loop
loop = asyncio.new_event_loop()
print(loop)
loop.run_until_complete(say('hello world', 1))
loop.close()