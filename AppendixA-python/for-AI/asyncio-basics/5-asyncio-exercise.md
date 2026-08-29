## Asyncio Basics Exercise

### Phase 1: Coroutine Objects

**Question:** Given the definition 
```
async def func(): 
  pass
```
, you execute the statement
```
obj = func()
```

* What is the exact type of `obj`? (try this)
* At the moment of this assignment, has any code within the body of `func` been executed?
* What happens to this object if it is never passed to a loop or awaited?

### Phase 2: Loop Initialization and Lifecycles

**Exercise 1: Implicit Management**
Write a script that executes an entry-point coroutine using `asyncio.run()`.

* Explain the specific sequence of loop creation, task wrapping, and loop closure that occurs during this call.

**Exercise 2: Explicit Management**
Write a script that performs the following:

1. Initialize an event loop object using `asyncio.new_event_loop()`.
2. Use this loop to execute a coroutine until completion.
3. Keep the loop object alive after execution finishes.
4. Finally, perform the manual steps required to destroy the loop and release its resources.

### Phase 3: Task Scheduling and Queues

**Exercise 3: Non-Blocking Insertion**
Inside an active asynchronous function, you have a coroutine that performs an I/O operation.

* Write the code to instantiate a `Task` object for this coroutine.
* Describe the state of the **Ready Queue** immediately after this instantiation.
* Write a sequence where the current execution flow proceeds to a subsequent `print()` statement without yielding control back to the loop for the new Task.

### Phase 4: Synchronization of Multiple Tasks

**Exercise 4: Concurrent Aggregation**
You have three separate coroutines.

* Write a solution that ensures all three are registered as Tasks in the event loop.
* Use the standard library utility to pause the execution of the current frame until all three tasks transition to the "Done" state.
* Ensure that the results (return values) of all three tasks are captured in a single variable.

### Phase 5: Execution Environment Restrictions

**Exercise 5: Global Scope Limitations**
Write a script that attempts to call `asyncio.create_task()` directly at the top level of a `.py` file (outside of any function).

* Identify the exact `Exception` type raised.
* Explain why the `Task` constructor requires a reference to a `running` loop, and why it cannot simply store the task for a future loop that might be created later.

