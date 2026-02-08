import asyncio

async def say(what, when):
    await asyncio.sleep(when)
    print(what)

# When you call a coroutine the code inside of it is not executed
# Instead - it returns a corouting object
# Also = there will be an error generated when the destructor for the corouting object called - and it was not waited on.
# ret = say('hello', 3)    #say 
# print(ret)

print('Starting')
asyncio.run(say('hello', 5))   # This is where the event loop was created, and finnaly closed


