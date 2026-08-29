Review exercises

Make sure you are ready by handling with these challenges:


"""
EXERCISE 1: Understanding Python Objects, References, and Immutability
========================================================================

Your task:
Write a function that demonstrates the difference between mutable and immutable types.

Requirements:
- Create a function that takes a tuple and a list as parameters
- Attempt to modify the tuple (should fail)
- Modify the list
- Catch the exception when modifying the tuple
- Return a dictionary with keys: "tuple_error", "list_modified", "id_changed"
- The values should be: exception type as string, the modified list, and bool for id change

Hints:
- Use try/except blocks
- Use type().__name__ to get type name as string
- Compare object ids before and after modification
- Remember: tuples are immutable, lists are mutable

Example call:
  result = modify_collections((1, 2, 3), [4, 5, 6])
  # result["tuple_error"] should contain exception type
  # result["list_modified"] should be [4, 5, 6, 7] or similar
  # result["id_changed"] should indicate if list's id changed


EXERCISE 2: Data Structures, Slicing, and Comprehensions
=========================================================

Your task:
Process user data using slicing, comprehensions, and dictionary operations.

Requirements:
- Create a function that takes a list of names and a list of scores (parallel lists)
- Use slicing to get the first 3 records and last 2 records
- Use unpacking to separate a tuple of (min_score, max_score)
- Use a list comprehension to filter names where score >= threshold
- Return a dict with keys: "first_three", "last_two", "above_threshold"
- Each value should be a list of (name, score) tuples

Hints:
- Unpacking: min_score, max_score = (0, 100)
- Slicing works on lists: names[start:end]
- Comprehension syntax: [x for x in list if condition]
- You can zip two lists together

Example call:
  names = ["Alice", "Bob", "Charlie", "David", "Eve"]
  scores = [85, 92, 78, 88, 76]
  result = process_user_data(names, scores, 80)
  # result["above_threshold"] should contain tuples with score >= 80


EXERCISE 3: Virtual Environment, External Library, and File I/O
===============================================================

Your task:
Create a program that fetches data from an API and saves it to a text file.

Setup Instructions:
1. Create a virtual environment: python -m venv venv_agents
2. Activate it:
   - Linux/Mac: source venv_agents/bin/activate
   - Windows: venv_agents\Scripts\activate
3. Install requests: pip install requests

Program Requirements:
- Create a function that uses the requests library (external, no decorators)
- Fetch JSON data from a public API (e.g., https://jsonplaceholder.typicode.com/users/1)
- Save the response text to a file called "api_response.txt"
- Handle exceptions if the request fails
- Create another function that reads the file back and returns it as a string
- Return a tuple: (success_bool, content_string)

Hints:
- import requests (do this after activating venv)
- requests.get(url) returns a response object
- response.status_code should be 200 for success
- Open files with: open(filename, mode) where mode is 'w' for write, 'r' for read
- Use with statement: with open(...) as f:
- Try/except for network errors

Example call:
  success, content = fetch_and_save_api_data("https://jsonplaceholder.typicode.com/users/1")
  # If successful, success=True and content contains the JSON data as string
  # If failed, success=False and content contains error message
"""
